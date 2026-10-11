"""Comprehensive Unit & Integration Tests for Save The Serve (S.T.S) Donation Lifecycle

Covers:
1. Pydantic validation:
   - Physical donations: Cooked food, groceries, clothes, blankets, medical, and custom text ("other").
   - Perishable constraints: prepared_at and expires_at rules.
   - Direct monetary donations: Currency, amount, target NGO.
   - Earmarked monetary donations: Item name, cost per unit, total funded, auto unit calculation, and math consistency.
   - Unified discriminated union with explicit and inferred kinds.
2. Matching Engine & Geospatial Urgency:
   - Urgency calculations (critical, high, normal).
3. FastAPI Endpoints (TestClient + dependency injection overrides):
   - POST /donations (physical, direct monetary, earmarked monetary).
   - GET /donations/feed (geospatial feed with category, radius, urgency filters and role guards).
   - POST /donations/{id}/claim (15-minute reservation concurrency lock, conflict on concurrent claim, expired food rejection).
   - POST /donations/earmarked-fund (escrow intent generation).
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.core.database import create_point_geography
from app.main import app
from app.models.donation import Donation
from app.models.enums import DonationKind, DonationStatus, ItemCategory, UserRole
from app.models.ngo import NGODetail
from app.models.profile import Profile
from app.schemas.donation import (
    DirectMonetaryDonationCreate,
    DonationCreateRequest,
    EarmarkedFundRequest,
    EarmarkedMonetaryDonationCreate,
    PhysicalDonationCreate,
)
from app.schemas.profile import CoordinateSchema
from app.services.matching_engine import MatchedDonation, calculate_urgency_level
from pydantic import TypeAdapter


def test_physical_cooked_food_requires_expiry():
    """Verify cooked food is automatically perishable and requires a valid expires_at."""
    now = datetime.now(timezone.utc)
    coords = CoordinateSchema(longitude=-122.4194, latitude=37.7749)

    with pytest.raises(ValueError, match="require an explicit 'expires_at' deadline"):
        PhysicalDonationCreate(
            category=ItemCategory.COOKED_FOOD,
            title="Fresh Vegetable Soup",
            quantity_amount=Decimal("20.0"),
            quantity_unit="servings",
            pickup_address="100 Market St, SF",
            pickup_location=coords,
            is_perishable=False,
            expires_at=None,
        )

    with pytest.raises(ValueError, match="'expires_at' must be subsequent to 'prepared_at'"):
        PhysicalDonationCreate(
            category=ItemCategory.COOKED_FOOD,
            title="Fresh Vegetable Soup",
            quantity_amount=Decimal("20.0"),
            quantity_unit="servings",
            pickup_address="100 Market St, SF",
            pickup_location=coords,
            prepared_at=now,
            expires_at=now - timedelta(hours=1),
        )

    valid_food = PhysicalDonationCreate(
        category=ItemCategory.COOKED_FOOD,
        title="Fresh Vegetable Soup",
        quantity_amount=Decimal("20.0"),
        quantity_unit="servings",
        pickup_address="100 Market St, SF",
        pickup_location=coords,
        prepared_at=now,
        expires_at=now + timedelta(hours=4),
    )
    assert valid_food.is_perishable is True
    assert valid_food.category == ItemCategory.COOKED_FOOD


def test_physical_categories_groceries_clothes_blankets_medical():
    """Verify physical supply categories (groceries, clothes, blankets, medical)."""
    coords = CoordinateSchema(longitude=-122.4194, latitude=37.7749)

    grocery = PhysicalDonationCreate(
        category=ItemCategory.GROCERY,
        title="Rice & Lentils Sack",
        quantity_amount=Decimal("50.0"),
        quantity_unit="kg",
        pickup_address="123 Warehouse Rd",
        pickup_location=coords,
    )
    assert grocery.category == ItemCategory.GROCERY
    assert grocery.is_perishable is False

    clothes = PhysicalDonationCreate(
        category=ItemCategory.CLOTHES,
        title="Winter Sweaters",
        quantity_amount=Decimal("30"),
        quantity_unit="items",
        pickup_address="123 Warehouse Rd",
        pickup_location=coords,
    )
    assert clothes.category == ItemCategory.CLOTHES

    blanket = PhysicalDonationCreate(
        category=ItemCategory.BLANKET,
        title="Thermal Fleece Blankets",
        quantity_amount=Decimal("40"),
        quantity_unit="pieces",
        pickup_address="123 Warehouse Rd",
        pickup_location=coords,
    )
    assert blanket.category == ItemCategory.BLANKET

    medical = PhysicalDonationCreate(
        category=ItemCategory.MEDICAL,
        title="First Aid Trauma Kits",
        quantity_amount=Decimal("15"),
        quantity_unit="kits",
        pickup_address="123 Warehouse Rd",
        pickup_location=coords,
    )
    assert medical.category == ItemCategory.MEDICAL


def test_physical_category_other_requires_description_or_custom_text():
    """Verify category 'other' requires description or custom text note."""
    coords = CoordinateSchema(longitude=-122.4194, latitude=37.7749)

    with pytest.raises(ValueError, match="category is 'other'"):
        PhysicalDonationCreate(
            category=ItemCategory.OTHER,
            title="Miscellaneous Supplies",
            quantity_amount=Decimal("5.0"),
            quantity_unit="boxes",
            pickup_address="100 Market St, SF",
            pickup_location=coords,
            description=None,
            custom_category_note=None,
        )

    other_with_note = PhysicalDonationCreate(
        category=ItemCategory.OTHER,
        title="Hygiene Kits",
        quantity_amount=Decimal("5.0"),
        quantity_unit="boxes",
        pickup_address="100 Market St, SF",
        pickup_location=coords,
        custom_category_note="Disaster hygiene care kits containing soap and towels",
    )
    assert other_with_note.category == ItemCategory.OTHER
    assert "Disaster hygiene" in other_with_note.custom_category_note

    other_with_text = PhysicalDonationCreate(
        category=ItemCategory.OTHER,
        title="Hygiene Kits",
        quantity_amount=Decimal("5.0"),
        quantity_unit="boxes",
        pickup_address="100 Market St, SF",
        pickup_location=coords,
        custom_text="Sanitary products and toothbrushes",
    )
    assert other_with_text.custom_category_note == "Sanitary products and toothbrushes"


def test_direct_monetary_donation_schema():
    """Verify direct monetary donation fields and validations."""
    ngo_id = uuid.uuid4()
    monetary = DirectMonetaryDonationCreate(
        amount=Decimal("250.00"),
        currency="USD",
        target_ngo_id=ngo_id,
        donor_note="Support for emergency evening meals.",
    )
    assert monetary.amount == Decimal("250.00")
    assert monetary.currency == "USD"
    assert monetary.target_ngo_id == ngo_id
    assert monetary.kind == DonationKind.MONETARY_DIRECT


def test_earmarked_monetary_donation_math_and_auto_unit_calculation():
    """Verify earmarked donations calculate units if omitted and validate math if provided."""
    ngo_id = uuid.uuid4()

    earmarked = EarmarkedMonetaryDonationCreate(
        item_name="50 Blankets",
        units_count=50,
        cost_per_unit=Decimal("10.00"),
        total_amount_funded=Decimal("500.00"),
        target_ngo_id=ngo_id,
    )
    assert earmarked.units_count == 50
    assert earmarked.total_amount_funded == Decimal("500.00")

    auto_earmarked = EarmarkedMonetaryDonationCreate(
        item_name="50 Blankets",
        cost_per_unit=Decimal("10.00"),
        total_amount_funded=Decimal("500.00"),
        target_ngo_id=ngo_id,
    )
    assert auto_earmarked.units_count == 50

    with pytest.raises(ValueError, match="must be an exact multiple"):
        EarmarkedMonetaryDonationCreate(
            item_name="50 Blankets",
            cost_per_unit=Decimal("10.00"),
            total_amount_funded=Decimal("505.50"),
            target_ngo_id=ngo_id,
        )

    with pytest.raises(ValueError, match="does not match"):
        EarmarkedMonetaryDonationCreate(
            item_name="50 Blankets",
            units_count=50,
            cost_per_unit=Decimal("10.00"),
            total_amount_funded=Decimal("999.00"),
            target_ngo_id=ngo_id,
        )


def test_earmarked_escrow_fund_request():
    """Verify earmarked escrow fund intent request."""
    ngo_id = uuid.uuid4()
    req = EarmarkedFundRequest(
        item_name="Winter Jackets",
        units_count=20,
        cost_per_unit=Decimal("25.00"),
        total_amount_funded=Decimal("500.00"),
        target_ngo_id=ngo_id,
    )
    assert req.units_count == 20
    assert req.total_amount_funded == Decimal("500.00")


def test_unified_donation_create_request_union():
    """Verify DonationCreateRequest union handles explicit and inferred kinds."""
    ta = TypeAdapter(DonationCreateRequest)
    ngo_id = str(uuid.uuid4())

    parsed_phys = ta.validate_python({
        "category": "clothes",
        "title": "Winter Coats",
        "quantity_amount": 10,
        "quantity_unit": "pcs",
        "pickup_address": "123 St, SF",
        "pickup_location": {"longitude": -122.4, "latitude": 37.7},
    })
    assert isinstance(parsed_phys, PhysicalDonationCreate)
    assert parsed_phys.kind == DonationKind.PHYSICAL_ITEM

    parsed_monetary = ta.validate_python({
        "amount": 150.0,
        "target_ngo_id": ngo_id,
    })
    assert isinstance(parsed_monetary, DirectMonetaryDonationCreate)
    assert parsed_monetary.kind == DonationKind.MONETARY_DIRECT

    parsed_earmarked = ta.validate_python({
        "item_name": "50 Blankets",
        "cost_per_unit": 10.0,
        "total_amount_funded": 500.0,
        "target_ngo_id": ngo_id,
    })
    assert isinstance(parsed_earmarked, EarmarkedMonetaryDonationCreate)
    assert parsed_earmarked.kind == DonationKind.MONETARY_EARMARKED
    assert parsed_earmarked.units_count == 50


def test_matching_engine_urgency_levels():
    """Verify urgency level calculations: critical (< 3h), high (< 6h), normal (> 6h)."""
    now = datetime.now(timezone.utc)

    assert calculate_urgency_level(is_perishable=False, expiry_time=None, now_dt=now) == "normal"

    crit_time = now + timedelta(hours=2)
    assert calculate_urgency_level(is_perishable=True, expiry_time=crit_time, now_dt=now) == "critical"

    high_time = now + timedelta(hours=4, minutes=30)
    assert calculate_urgency_level(is_perishable=True, expiry_time=high_time, now_dt=now) == "high"

    normal_time = now + timedelta(hours=12)
    assert calculate_urgency_level(is_perishable=True, expiry_time=normal_time, now_dt=now) == "normal"


@pytest.fixture
def mock_donor_user():
    return Profile(
        id=uuid.uuid4(),
        email="donor@sts.org",
        role=UserRole.DONOR,
        full_name="Generous Donor",
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def mock_ngo_user():
    ngo_profile_id = uuid.uuid4()
    ngo_details = NGODetail(
        id=uuid.uuid4(),
        profile_id=ngo_profile_id,
        organization_name="Community Food Bank",
        registration_number="NGO-998811",
        operating_radius_km=Decimal("30.00"),
        hq_location=create_point_geography(-122.4194, 37.7749),
        is_approved=True,
        contact_email="contact@foodbank.org",
        contact_phone="+14155551234",
    )
    user = Profile(
        id=ngo_profile_id,
        email="ngo@sts.org",
        role=UserRole.NGO,
        full_name="NGO Coordinator",
        is_active=True,
        is_verified=True,
    )
    user.ngo_details = ngo_details
    return user


@pytest.fixture
def mock_driver_user():
    return Profile(
        id=uuid.uuid4(),
        email="driver@sts.org",
        role=UserRole.DRIVER,
        full_name="Rapid Dispatch Driver",
        location=create_point_geography(-122.4200, 37.7750),
        is_active=True,
        is_verified=True,
    )


def test_endpoint_create_physical_donation(mock_donor_user):
    """Test POST /donations for physical item."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: mock_donor_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    payload = {
        "kind": "physical_item",
        "category": "clothes",
        "title": "Winter Fleeces & Beanies",
        "quantity_amount": 25,
        "quantity_unit": "pieces",
        "pickup_address": "789 Howard St, SF",
        "pickup_location": {"longitude": -122.405, "latitude": 37.785},
    }
    response = client.post("/api/v1/donations", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Winter Fleeces & Beanies"
    assert data["status"] == "available"
    assert data["kind"] == "physical_item"
    assert data["pickup_location"]["longitude"] == -122.405
    assert data["pickup_location"]["latitude"] == 37.785


def test_endpoint_create_direct_monetary_donation(mock_donor_user, mock_ngo_user):
    """Test POST /donations for direct monetary relief."""
    target_ngo = mock_ngo_user.ngo_details
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = target_ngo
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: mock_donor_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    payload = {
        "kind": "monetary_direct",
        "amount": 250.00,
        "currency": "USD",
        "target_ngo_id": str(target_ngo.id),
        "donor_note": "Emergency relief support",
    }
    response = client.post("/api/v1/donations", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["kind"] == "monetary_direct"
    assert data["status"] == "completed"
    assert float(data["quantity_amount"]) == 250.00
    assert data["monetary_currency"] == "USD"
    assert data["assigned_ngo_id"] == str(target_ngo.id)


def test_endpoint_create_earmarked_monetary_donation(mock_donor_user, mock_ngo_user):
    """Test POST /donations for earmarked aid."""
    target_ngo = mock_ngo_user.ngo_details
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = target_ngo
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: mock_donor_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    payload = {
        "kind": "monetary_earmarked",
        "item_name": "50 Blankets",
        "cost_per_unit": 10.0,
        "total_amount_funded": 500.0,
        "target_ngo_id": str(target_ngo.id),
        "donor_note": "For homeless shelter winter prep",
    }
    response = client.post("/api/v1/donations", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["kind"] == "monetary_earmarked"
    assert data["status"] == "available"
    assert data["earmarked_cause"] == "50 Blankets"
    assert float(data["quantity_amount"]) == 500.00


def test_endpoint_donations_feed_role_guard(mock_donor_user):
    """Verify that regular donors cannot access GET /donations/feed (only NGO & Driver)."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: mock_donor_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    response = client.get("/api/v1/donations/feed?lat=37.77&lon=-122.41")
    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_endpoint_donations_feed_success(mock_ngo_user, monkeypatch):
    """Test GET /donations/feed for authorized NGO with radius and category filtering."""
    mock_db = AsyncMock()
    now = datetime.now(timezone.utc)

    test_donation = Donation(
        id=uuid.uuid4(),
        donor_id=uuid.uuid4(),
        kind=DonationKind.PHYSICAL_ITEM,
        category=ItemCategory.COOKED_FOOD,
        status=DonationStatus.AVAILABLE,
        title="100 Meal Packs",
        quantity_amount=Decimal("100"),
        quantity_unit="servings",
        pickup_address="500 Pine St, SF",
        pickup_location=create_point_geography(-122.408, 37.791),
        is_perishable=True,
        prepared_at=now,
        expiry_time=now + timedelta(hours=2),
        created_at=now,
        updated_at=now,
    )
    mock_matched = [
        MatchedDonation(
            donation=test_donation,
            distance_km=1.25,
            urgency_level="critical",
            is_claimable=True,
        )
    ]

    async def mock_find_nearby(*args, **kwargs):
        return mock_matched

    from app.api.v1.endpoints import donations as donations_ep
    monkeypatch.setattr(donations_ep, "find_nearby_donations", mock_find_nearby)

    app.dependency_overrides[get_current_user] = lambda: mock_ngo_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    response = client.get(
        "/api/v1/donations/feed",
        params={
            "lat": 37.7749,
            "lon": -122.4194,
            "radius_km": 15.0,
            "category": "cooked_food",
            "urgency": "critical",
        },
    )
    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert len(items) == 1
    assert items[0]["title"] == "100 Meal Packs"
    assert items[0]["distance_km"] == 1.25
    assert items[0]["urgency_level"] == "critical"
    assert items[0]["is_claimable"] is True


def test_endpoint_claim_donation_success(mock_ngo_user):
    """Test POST /donations/{id}/claim by verified NGO applies a 15-minute lock."""
    donation_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    donation_record = Donation(
        id=donation_id,
        donor_id=uuid.uuid4(),
        kind=DonationKind.PHYSICAL_ITEM,
        category=ItemCategory.COOKED_FOOD,
        status=DonationStatus.AVAILABLE,
        title="Fresh Cooked Meals",
        quantity_amount=Decimal("30"),
        quantity_unit="portions",
        is_perishable=True,
        expiry_time=now + timedelta(hours=5),
        created_at=now,
        updated_at=now,
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = donation_record
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: mock_ngo_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    response = client.post(f"/api/v1/donations/{donation_id}/claim")
    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["donation_id"] == str(donation_id)
    assert data["status"] == "reserved"
    assert data["reservation_lock_minutes"] == 15
    assert "reserved_until" in data
    assert donation_record.status == DonationStatus.RESERVED
    assert donation_record.assigned_ngo_id == mock_ngo_user.ngo_details.id


def test_endpoint_claim_donation_conflict_on_active_lock(mock_ngo_user):
    """Test claiming an item already locked by another NGO returns 409 Conflict."""
    donation_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    other_ngo_id = uuid.uuid4()

    locked_donation = Donation(
        id=donation_id,
        donor_id=uuid.uuid4(),
        kind=DonationKind.PHYSICAL_ITEM,
        category=ItemCategory.COOKED_FOOD,
        status=DonationStatus.RESERVED,
        assigned_ngo_id=other_ngo_id,
        reserved_until=now + timedelta(minutes=10),
        title="Warm Soup Batch",
        quantity_amount=Decimal("40"),
        quantity_unit="servings",
        created_at=now,
        updated_at=now,
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = locked_donation
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: mock_ngo_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    response = client.post(f"/api/v1/donations/{donation_id}/claim")
    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "currently locked by another NGO" in response.json()["detail"]


def test_endpoint_claim_expired_perishable_food(mock_ngo_user):
    """Test attempting to claim expired perishable food returns 410 Gone."""
    donation_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    expired_donation = Donation(
        id=donation_id,
        donor_id=uuid.uuid4(),
        kind=DonationKind.PHYSICAL_ITEM,
        category=ItemCategory.COOKED_FOOD,
        status=DonationStatus.AVAILABLE,
        is_perishable=True,
        expiry_time=now - timedelta(minutes=30),
        title="Past-due Sandwich Trays",
        quantity_amount=Decimal("20"),
        quantity_unit="servings",
        created_at=now,
        updated_at=now,
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expired_donation
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: mock_ngo_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    response = client.post(f"/api/v1/donations/{donation_id}/claim")
    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_410_GONE
    assert "expired" in response.json()["detail"]


def test_endpoint_create_earmarked_escrow_fund_intent(mock_donor_user, mock_ngo_user):
    """Test POST /donations/earmarked-fund creates escrow purchasing intent."""
    target_ngo = mock_ngo_user.ngo_details
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = target_ngo
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_current_user] = lambda: mock_donor_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    payload = {
        "item_name": "50 Blankets",
        "units_count": 50,
        "cost_per_unit": 12.50,
        "total_amount_funded": 625.00,
        "target_ngo_id": str(target_ngo.id),
        "donor_note": "For the downtown winter drive",
    }
    response = client.post("/api/v1/donations/earmarked-fund", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["item_name"] == "50 Blankets"
    assert data["units_count"] == 50
    assert float(data["total_amount"]) == 625.00
    assert data["escrow_status"] == "intent_created"
    assert "escrow_pi_" in data["client_secret"]
    assert data["target_ngo_id"] == str(target_ngo.id)
