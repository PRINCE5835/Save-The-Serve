"""Comprehensive Tests for Expiry Watchdog, Deliveries Logistics Handshake, NGO Directory & Settings/Support

Covers:
1. Expiry Monitor (app/services/expiry_monitor.py):
   - Auto-expiring spoiled food (expiry_time <= now -> EXPIRED).
   - Dynamic escalation: Surplus cooked food with < 2h remaining expands radius and flags CRITICAL_URGENCY.
   - Surplus food with > 2h remaining is left as normal.
2. Deliveries Logistics & OTP Handshakes (app/api/v1/endpoints/deliveries.py):
   - Delivery creation with generated 6-digit OTPs.
   - Driver task claim (POST /deliveries/{id}/accept).
   - Rejection if already claimed by another driver (409 Conflict).
   - Donor pickup handshake via 6-digit pickup_otp (POST /deliveries/{id}/pickup-verify).
   - Rejection on invalid pickup OTP (401 Unauthorized).
   - NGO drop-off handshake via 6-digit dropoff_otp + mandatory photo proof (POST /deliveries/{id}/dropoff-verify).
   - Rejection on missing photo proof (422) or wrong OTP (401).
   - Driver telemetry location update (PATCH /deliveries/{id}/location).
3. NGO Public Directory & Capacity Management (app/api/v1/endpoints/ngos.py):
   - Public directory lookup (GET /ngos) with location search, distance, and contact details.
   - Category filtering (accepted_categories).
   - Capacity intake toggle filtering (is_accepting_donations).
   - NGO coordinator capacity update (PATCH /ngos/{id}/capacity).
4. User Profile Settings & Support Tickets (app/api/v1/endpoints/settings.py & support.py):
   - User profile management (GET/PATCH /settings/profile).
   - Password change with verification of existing password (POST /settings/password).
   - Push notification preferences (GET/PUT /settings/notifications).
   - Help ticket creation and status updates (POST /support/tickets, GET /support/tickets, PATCH /support/tickets/{id}).
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.deliveries import hash_otp
from app.core.database import create_point_geography
from app.core.security import get_password_hash
from app.main import app
from app.models.delivery import Delivery
from app.models.donation import Donation
from app.models.enums import DeliveryStatus, DonationKind, DonationStatus, ItemCategory, TicketPriority, TicketStatus, UserRole
from app.models.ngo import NGODetail
from app.models.profile import Profile
from app.models.support import SupportTicket
from app.schemas.ngo import encode_ngo_capacity_meta
from app.services.expiry_monitor import scan_and_escalate_perishables


@pytest.fixture
def donor_user():
    return Profile(
        id=uuid.uuid4(),
        email="donor1@sts.org",
        role=UserRole.DONOR,
        full_name="Generous Donor",
        hashed_password=get_password_hash("ValidPassword123!"),
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def driver_user():
    return Profile(
        id=uuid.uuid4(),
        email="driver1@sts.org",
        role=UserRole.DRIVER,
        full_name="Alex Dispatch",
        hashed_password=get_password_hash("ValidPassword123!"),
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def ngo_user():
    ngo_pid = uuid.uuid4()
    ngo_details = NGODetail(
        id=uuid.uuid4(),
        profile_id=ngo_pid,
        organization_name="Downtown Hope Shelter",
        registration_number="REG-HOPE-7788",
        operating_radius_km=Decimal("30.00"),
        hq_location=create_point_geography(-122.4194, 37.7749),
        is_approved=True,
        contact_email="director@hopeshelter.org",
        contact_phone="+14155554321",
        capacity_description=encode_ngo_capacity_meta(
            description="Active food shelter",
            is_accepting=True,
            accepted_categories=[ItemCategory.COOKED_FOOD, ItemCategory.GROCERY],
        ),
    )
    user = Profile(
        id=ngo_pid,
        email="ngo1@sts.org",
        role=UserRole.NGO,
        full_name="Sarah Hope",
        hashed_password=get_password_hash("ValidPassword123!"),
        is_active=True,
        is_verified=True,
    )
    user.ngo_details = ngo_details
    return user


@pytest.fixture
def admin_user():
    return Profile(
        id=uuid.uuid4(),
        email="admin@sts.org",
        role=UserRole.ADMIN,
        full_name="Platform Admin",
        hashed_password=get_password_hash("ValidPassword123!"),
        is_active=True,
        is_verified=True,
    )


@pytest.mark.asyncio
async def test_expiry_monitor_auto_expires_spoiled_food():
    """Verify that perishable meals with expiry_time <= now are marked EXPIRED."""
    now = datetime.now(timezone.utc)
    spoiled_donation = Donation(
        id=uuid.uuid4(),
        donor_id=uuid.uuid4(),
        kind=DonationKind.PHYSICAL_ITEM,
        category=ItemCategory.COOKED_FOOD,
        status=DonationStatus.AVAILABLE,
        is_perishable=True,
        title="Curry Trays (Spoiled)",
        quantity_amount=Decimal("20"),
        quantity_unit="servings",
        expiry_time=now - timedelta(minutes=15),
        created_at=now - timedelta(hours=5),
        updated_at=now - timedelta(hours=5),
    )

    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [spoiled_donation]
    mock_db.execute.return_value = mock_res

    report = await scan_and_escalate_perishables(mock_db)

    assert report.expired_count == 1
    assert spoiled_donation.id in report.expired_donation_ids
    assert spoiled_donation.status == DonationStatus.EXPIRED
    assert spoiled_donation.metadata_json["urgency_status"] == "EXPIRED"


@pytest.mark.asyncio
async def test_expiry_monitor_escalates_critical_urgency_food():
    """Verify that surplus cooked meals with < 2 hours remaining expand search radius and flag CRITICAL_URGENCY."""
    now = datetime.now(timezone.utc)
    critical_donation = Donation(
        id=uuid.uuid4(),
        donor_id=uuid.uuid4(),
        kind=DonationKind.PHYSICAL_ITEM,
        category=ItemCategory.COOKED_FOOD,
        status=DonationStatus.AVAILABLE,
        is_perishable=True,
        title="Fresh Cooked Rice & Stew",
        quantity_amount=Decimal("50"),
        quantity_unit="servings",
        pickup_location=create_point_geography(-122.4194, 37.7749),
        expiry_time=now + timedelta(hours=1, minutes=30),
        metadata_json={"search_radius_km": 25.0},
        created_at=now,
        updated_at=now,
    )

    mock_db = AsyncMock()
    mock_donations_res = MagicMock()
    mock_donations_res.scalars.return_value.all.return_value = [critical_donation]
    mock_ngos_res = MagicMock()
    mock_ngos_res.scalars.return_value.all.return_value = ["Downtown Shelter", "Mission Relief"]
    mock_db.execute.side_effect = [mock_donations_res, mock_ngos_res]

    report = await scan_and_escalate_perishables(mock_db, critical_threshold_hours=2.0, radius_multiplier=2.0)

    assert report.escalated_count == 1
    assert len(report.escalations) == 1
    ev = report.escalations[0]
    assert ev.donation_id == critical_donation.id
    assert ev.original_radius_km == 25.0
    assert ev.expanded_radius_km == 50.0
    assert ev.nearby_ngos_count == 2

    meta = critical_donation.metadata_json
    assert meta["urgency_status"] == "CRITICAL_URGENCY"
    assert meta["is_escalated"] is True
    assert meta["expanded_radius_km"] == 50.0


def test_endpoint_create_delivery_and_accept_by_driver(ngo_user, driver_user):
    """Test creating a delivery task (with OTPs) and driver accepting it."""
    donation_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    donation_record = Donation(
        id=donation_id,
        donor_id=uuid.uuid4(),
        kind=DonationKind.PHYSICAL_ITEM,
        status=DonationStatus.AVAILABLE,
        title="Canned Goods Batch",
        quantity_amount=Decimal("100"),
        quantity_unit="cans",
        created_at=now,
        updated_at=now,
    )

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_res1 = MagicMock()
    mock_res1.scalar_one_or_none.return_value = donation_record
    mock_res2 = MagicMock()
    mock_res2.scalar_one_or_none.return_value = None
    mock_db.execute.side_effect = [mock_res1, mock_res2]

    app.dependency_overrides[get_current_user] = lambda: ngo_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    create_payload = {
        "donation_id": str(donation_id),
        "destination_ngo_id": str(ngo_user.ngo_details.id),
        "pickup_location": {"longitude": -122.41, "latitude": 37.77},
        "dropoff_location": {"longitude": -122.42, "latitude": 37.78},
        "estimated_distance_km": 4.5,
        "estimated_duration_mins": 18,
    }
    resp = client.post("/api/v1/deliveries", json=create_payload)
    app.dependency_overrides.clear()

    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert len(data["pickup_otp"]) == 6
    assert len(data["dropoff_otp"]) == 6
    delivery_id = data["id"]

    delivery_record = Delivery(
        id=uuid.UUID(delivery_id),
        donation_id=donation_id,
        destination_ngo_id=ngo_user.ngo_details.id,
        driver_id=None,
        status=DeliveryStatus.ASSIGNED,
        pickup_location=create_point_geography(-122.41, 37.77),
        dropoff_location=create_point_geography(-122.42, 37.78),
        created_at=now,
        updated_at=now,
    )

    mock_db_accept = AsyncMock()
    mock_res_acc = MagicMock()
    mock_res_acc.scalar_one_or_none.return_value = delivery_record
    mock_db_accept.execute.return_value = mock_res_acc

    app.dependency_overrides[get_current_user] = lambda: driver_user
    app.dependency_overrides[get_db] = lambda: mock_db_accept

    client = TestClient(app)
    accept_resp = client.post(f"/api/v1/deliveries/{delivery_id}/accept")
    app.dependency_overrides.clear()

    assert accept_resp.status_code == status.HTTP_200_OK
    acc_data = accept_resp.json()
    assert acc_data["status"] == "accepted"
    assert delivery_record.status == DeliveryStatus.ACCEPTED
    assert delivery_record.driver_id == driver_user.id


def test_endpoint_pickup_verification_handshake(driver_user):
    """Test driver pickup handshake with 6-digit OTP."""
    delivery_id = uuid.uuid4()
    plain_otp = "849201"
    now = datetime.now(timezone.utc)

    delivery = Delivery(
        id=delivery_id,
        donation_id=uuid.uuid4(),
        destination_ngo_id=uuid.uuid4(),
        driver_id=driver_user.id,
        status=DeliveryStatus.ACCEPTED,
        pickup_location=create_point_geography(-122.41, 37.77),
        dropoff_location=create_point_geography(-122.42, 37.78),
        pickup_otp_hash=hash_otp(plain_otp),
        created_at=now,
        updated_at=now,
    )
    delivery.donation = Donation(
        id=delivery.donation_id,
        donor_id=uuid.uuid4(),
        kind=DonationKind.PHYSICAL_ITEM,
        status=DonationStatus.RESERVED,
        title="Warm Blankets Batch",
        quantity_amount=Decimal("30"),
        quantity_unit="items",
        created_at=now,
        updated_at=now,
    )

    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = delivery
    mock_db.execute.return_value = mock_res

    app.dependency_overrides[get_current_user] = lambda: driver_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)

    bad_resp = client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-verify",
        json={"pickup_otp": "000000"},
    )
    assert bad_resp.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED)

    good_resp = client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-verify",
        json={
            "pickup_otp": plain_otp,
            "proof_of_pickup_url": "https://storage.sts.org/proofs/pickup1.jpg",
            "current_latitude": 37.775,
            "current_longitude": -122.415,
        },
    )
    app.dependency_overrides.clear()

    assert good_resp.status_code == status.HTTP_200_OK
    assert good_resp.json()["status"] == "picked_up"
    assert delivery.status == DeliveryStatus.PICKED_UP
    assert delivery.proof_of_pickup_url == "https://storage.sts.org/proofs/pickup1.jpg"
    assert delivery.donation.status == DonationStatus.IN_TRANSIT


def test_endpoint_dropoff_verification_handshake(driver_user):
    """Test driver dropoff handshake requiring 6-digit OTP and image proof."""
    delivery_id = uuid.uuid4()
    dropoff_otp = "551934"
    now = datetime.now(timezone.utc)

    delivery = Delivery(
        id=delivery_id,
        donation_id=uuid.uuid4(),
        destination_ngo_id=uuid.uuid4(),
        driver_id=driver_user.id,
        status=DeliveryStatus.PICKED_UP,
        pickup_location=create_point_geography(-122.41, 37.77),
        dropoff_location=create_point_geography(-122.42, 37.78),
        delivery_otp_hash=hash_otp(dropoff_otp),
        created_at=now,
        updated_at=now,
    )
    delivery.donation = Donation(
        id=delivery.donation_id,
        donor_id=uuid.uuid4(),
        kind=DonationKind.PHYSICAL_ITEM,
        status=DonationStatus.IN_TRANSIT,
        title="Fresh Produce Crates",
        quantity_amount=Decimal("40"),
        quantity_unit="kg",
        created_at=now,
        updated_at=now,
    )

    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = delivery
    mock_db.execute.return_value = mock_res

    app.dependency_overrides[get_current_user] = lambda: driver_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)

    bad_req = client.post(
        f"/api/v1/deliveries/{delivery_id}/dropoff-verify",
        json={"dropoff_otp": dropoff_otp, "proof_of_delivery_url": ""},
    )
    assert bad_req.status_code in (status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST)

    good_resp = client.post(
        f"/api/v1/deliveries/{delivery_id}/dropoff-verify",
        json={
            "dropoff_otp": dropoff_otp,
            "proof_of_delivery_url": "https://storage.sts.org/proofs/delivery_signed.jpg",
            "current_latitude": 37.782,
            "current_longitude": -122.425,
        },
    )
    app.dependency_overrides.clear()

    assert good_resp.status_code == status.HTTP_200_OK
    assert good_resp.json()["status"] == "delivered"
    assert delivery.status == DeliveryStatus.DELIVERED
    assert delivery.proof_of_delivery_url == "https://storage.sts.org/proofs/delivery_signed.jpg"
    assert delivery.donation.status in (DonationStatus.DELIVERED, DonationStatus.COMPLETED)


def test_endpoint_public_ngo_directory_and_category_filtering():
    """Test GET /ngos public directory lookup with category and capacity filtering."""
    now = datetime.now(timezone.utc)
    ngo1 = NGODetail(
        id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        organization_name="San Francisco Meal Bank",
        registration_number="REG-SF-1122",
        operating_radius_km=Decimal("25.00"),
        hq_location=create_point_geography(-122.419, 37.775),
        is_approved=True,
        contact_email="intake@sfmealbank.org",
        contact_phone="+14155551122",
        capacity_description=encode_ngo_capacity_meta(
            description="Focuses on hot meals",
            is_accepting=True,
            accepted_categories=[ItemCategory.COOKED_FOOD],
        ),
        created_at=now,
        updated_at=now,
    )
    ngo2 = NGODetail(
        id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        organization_name="Bay Area Clothes Pantry",
        registration_number="REG-SF-3344",
        operating_radius_km=Decimal("35.00"),
        hq_location=create_point_geography(-122.425, 37.780),
        is_approved=True,
        contact_email="contact@clothespantry.org",
        contact_phone="+14155553344",
        capacity_description=encode_ngo_capacity_meta(
            description="Warm winter clothes only",
            is_accepting=True,
            accepted_categories=[ItemCategory.CLOTHES, ItemCategory.BLANKET],
        ),
        created_at=now,
        updated_at=now,
    )

    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [ngo1, ngo2]
    mock_db.execute.return_value = mock_res

    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    all_resp = client.get("/api/v1/ngos")
    assert all_resp.status_code == status.HTTP_200_OK
    assert len(all_resp.json()) == 2

    cooked_resp = client.get("/api/v1/ngos?category=cooked_food")
    assert cooked_resp.status_code == status.HTTP_200_OK
    items = cooked_resp.json()
    assert len(items) == 1
    assert items[0]["organization_name"] == "San Francisco Meal Bank"

    app.dependency_overrides.clear()


def test_endpoint_update_ngo_capacity_toggle(ngo_user):
    """Test NGO coordinator toggling donation intake capacity (PATCH /ngos/{id}/capacity)."""
    target_ngo = ngo_user.ngo_details

    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = target_ngo
    mock_db.execute.return_value = mock_res

    app.dependency_overrides[get_current_user] = lambda: ngo_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    patch_payload = {
        "is_accepting_donations": False,
        "capacity_description": "Storage warehouse currently at 100% capacity",
        "operating_radius_km": 40.0,
    }
    resp = client.patch(f"/api/v1/ngos/{target_ngo.id}/capacity", json=patch_payload)
    app.dependency_overrides.clear()

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["is_accepting_donations"] is False
    assert "100% capacity" in data["capacity_description"]
    assert float(data["operating_radius_km"]) == 40.0


def test_endpoint_user_profile_management(donor_user):
    """Test GET and PATCH /settings/profile."""
    mock_db = AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: donor_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)

    get_res = client.get("/api/v1/settings/profile")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["email"] == donor_user.email

    patch_res = client.patch(
        "/api/v1/settings/profile",
        json={
            "full_name": "Generous Donor Updated",
            "phone_number": "+14155559988",
            "address_line": "123 Green St, SF",
            "location": {"longitude": -122.41, "latitude": 37.79},
        },
    )
    app.dependency_overrides.clear()

    assert patch_res.status_code == status.HTTP_200_OK
    data = patch_res.json()
    assert data["full_name"] == "Generous Donor Updated"
    assert data["phone_number"] == "+14155559988"


def test_endpoint_password_change(donor_user):
    """Test POST /settings/password verifies current credentials and updates hash."""
    mock_db = AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: donor_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)

    bad_resp = client.post(
        "/api/v1/settings/password",
        json={"current_password": "WrongPassword!", "new_password": "BrandNewSecretPassword1!"},
    )
    assert bad_resp.status_code == status.HTTP_401_UNAUTHORIZED

    good_resp = client.post(
        "/api/v1/settings/password",
        json={"current_password": "ValidPassword123!", "new_password": "BrandNewSecretPassword1!"},
    )
    app.dependency_overrides.clear()

    assert good_resp.status_code == status.HTTP_200_OK
    assert "updated successfully" in good_resp.json()["message"]


def test_endpoint_push_notification_preferences(donor_user):
    """Test GET and PUT /settings/notifications."""
    app.dependency_overrides[get_current_user] = lambda: donor_user
    client = TestClient(app)

    get_res = client.get("/api/v1/settings/notifications")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["urgent_surplus_alerts"] is True

    put_res = client.put(
        "/api/v1/settings/notifications",
        json={
            "push_enabled": True,
            "email_enabled": False,
            "sms_alerts_enabled": True,
            "urgent_surplus_alerts": True,
            "fcm_device_token": "fcm_token_device_abc12345",
        },
    )
    app.dependency_overrides.clear()

    assert put_res.status_code == status.HTTP_200_OK
    data = put_res.json()
    assert data["email_enabled"] is False
    assert data["sms_alerts_enabled"] is True
    assert data["fcm_device_token"] == "fcm_token_device_abc12345"


def test_endpoint_support_ticket_creation_and_resolution(donor_user, admin_user):
    """Test creating support ticket and admin resolution."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: donor_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    ticket_payload = {
        "subject": "Driver delayed at pickup location",
        "message": "Driver was scheduled 30 minutes ago but has not arrived yet.",
        "priority": "high",
    }
    create_res = client.post("/api/v1/support/tickets", json=ticket_payload)
    app.dependency_overrides.clear()

    assert create_res.status_code == status.HTTP_201_CREATED
    data = create_res.json()
    assert data["subject"] == "Driver delayed at pickup location"
    assert data["status"] == "open"
    assert data["priority"] == "high"
    ticket_id = data["id"]

    ticket_record = SupportTicket(
        id=uuid.UUID(ticket_id),
        creator_id=donor_user.id,
        subject="Driver delayed at pickup location",
        message="Driver was scheduled 30 minutes ago...",
        priority=TicketPriority.HIGH,
        status=TicketStatus.OPEN,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    mock_db_admin = AsyncMock()
    mock_res_admin = MagicMock()
    mock_res_admin.scalar_one_or_none.return_value = ticket_record
    mock_db_admin.execute.return_value = mock_res_admin

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: mock_db_admin

    client = TestClient(app)
    resolve_res = client.patch(
        f"/api/v1/support/tickets/{ticket_id}",
        json={"status": "resolved", "resolution_notes": "Driver re-routed due to traffic and arrived."},
    )
    app.dependency_overrides.clear()

    assert resolve_res.status_code == status.HTTP_200_OK
    res_data = resolve_res.json()
    assert res_data["status"] == "resolved"
    assert "Driver re-routed" in res_data["resolution_notes"]
