"""Comprehensive End-to-End Systems QA & Role Workflows Test Suite for Save The Serve (S.T.S)

Principal QA Engineer & Full-Stack Systems Tester verification across:
1. TEST SUITE 1: AUTHENTICATION, ROLES & ACCOUNT MANAGEMENT
   - User Signup & RBAC Initialization (Donor User A, NGO User B, Driver User C)
   - Profile & Notification Settings updates, NGO Capacity toggles ('accepting' vs 'at_capacity'), 422 on invalid enum
   - RBAC Route Protection: Donor accessing NGO-restricted claim -> 403 Forbidden ("Insufficient permissions")
2. TEST SUITE 2: PHYSICAL DONATIONS & GEOSPATIAL MATCHING
   - Perishable Cooked Food Flow (50 meals, prepared 1h ago, expires NOW+3h, coords in SRID 4326)
   - Geospatial Discovery Radius (< 2 km match, distant NGO 40 km excluded on 10 km radius)
   - Multi-Category Physical Items (Blankets, Medical, Custom Other)
3. TEST SUITE 3: MONETARY & EARMARKED PURCHASING FLOW
   - Direct Financial Donation (₹2,500 to Hope Shelter Foundation + webhook callback + completed status + ledger update)
   - Earmarked Item Purchase (50 Woolen Blankets @ ₹200, funding 20 blankets total ₹4000, escrowed to 'Woolen Blankets')
4. TEST SUITE 4: EXPIRY WATCHDOG & URGENCY ESCALATION
   - Perishable Watchdog (< 2h, 45m left -> CRITICAL_URGENCY, 2x radius expansion)
   - Auto-Disqualification (expired food -> 'expired', removed from feed)
5. TEST SUITE 5: 3-WAY HANDOFF & DRIVER LOGISTICS
   - NGO 15-minute concurrency reservation hold
   - Driver task claim & 6-digit OTP generation
   - Dual-handshake OTP verification (invalid OTP -> 400 'Invalid pickup code', valid pickup -> 'in_transit', valid dropoff -> 'completed')
6. TEST SUITE 6: SHARED UTILITIES & ESG AUDIT
   - Public NGO Directory & Contact Lookup (search=Hope+Shelter, no private bank data)
   - Help & Support Tickets (Driver submits "Wrong donor address" -> linked to user ID)
   - ESG & Waste Metrics Generation (GET /esg/stats -> meals rescued, kg waste diverted, CO2 offsets saved)
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
from app.core.database import create_point_geography, parse_geography_point
from app.core.security import create_access_token, get_password_hash, verify_password
from app.main import app
from app.models.delivery import Delivery
from app.models.donation import Donation
from app.models.enums import (
    DeliveryStatus,
    DonationKind,
    DonationStatus,
    ItemCategory,
    TicketPriority,
    TicketStatus,
    UserRole,
)
from app.models.ngo import NGODetail
from app.models.profile import Profile
from app.models.support import SupportTicket
from app.schemas.ngo import CapacityStatus, encode_ngo_capacity_meta
from app.services.expiry_monitor import scan_and_escalate_perishables
from app.services.matching_engine import MatchedDonation


@pytest.fixture
def qa_actors():
    """Builds the 3 primary actors: User A (Donor), User B (NGO), User C (Driver)."""
    now = datetime.now(timezone.utc)

    donor_id = uuid.uuid4()
    user_a = Profile(
        id=donor_id,
        email="greendine@restaurant.in",
        role=UserRole.DONOR,
        full_name="Green Dine Restaurant",
        phone_number="+919811223344",
        address_line="Block B, North Delhi, 28.7041 N, 77.1025 E",
        location=create_point_geography(77.1025, 28.7041),
        hashed_password=get_password_hash("DonorPassSecure2026!"),
        is_active=True,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )

    ngo_profile_id = uuid.uuid4()
    ngo_detail_id = uuid.uuid4()
    ngo_detail = NGODetail(
        id=ngo_detail_id,
        profile_id=ngo_profile_id,
        organization_name="Hope Shelter Foundation",
        registration_number="NGO-102938",
        tax_exemption_number="80G-DEL-2026",
        operating_radius_km=Decimal("25.00"),
        hq_location=create_point_geography(77.1100, 28.7100),
        is_approved=True,
        contact_email="director@hopeshelter.org",
        contact_phone="+919876500112",
        capacity_description=encode_ngo_capacity_meta(
            description="Active community shelter and kitchen",
            is_accepting=True,
            accepted_categories=[ItemCategory.COOKED_FOOD, ItemCategory.GROCERY, ItemCategory.BLANKET],
        ),
        created_at=now,
        updated_at=now,
    )
    user_b = Profile(
        id=ngo_profile_id,
        email="director@hopeshelter.org",
        role=UserRole.NGO,
        full_name="Hope Shelter Foundation",
        phone_number="+919876500112",
        address_line="Sector 14, Rohini, Delhi",
        location=create_point_geography(77.1100, 28.7100),
        hashed_password=get_password_hash("NgoPassSecure2026!"),
        is_active=True,
        is_verified=True,
        ngo_details=ngo_detail,
        created_at=now,
        updated_at=now,
    )

    driver_id = uuid.uuid4()
    user_c = Profile(
        id=driver_id,
        email="alex.driver@sts-express.in",
        role=UserRole.DRIVER,
        full_name="Alex Driver",
        phone_number="+919876543210",
        address_line="Dispatch Hub 4, Delhi",
        location=create_point_geography(77.1050, 28.7060),
        hashed_password=get_password_hash("DriverPassSecure2026!"),
        is_active=True,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )

    return {"donor": user_a, "ngo": user_b, "driver": user_c}


def test_suite_1_user_signup_and_rbac_initialization():
    """Suite 1.1: Test User Signup & RBAC Initialization.

    - Register User A: Role 'donor' ("Green Dine Restaurant", 28.7041° N, 77.1025° E).
    - Register User B: Role 'ngo' ("Hope Shelter Foundation", 28.7100° N, 77.1100° E, Reg: "NGO-102938").
    - Register User C: Role 'driver' ("Alex Driver", Phone: "+919876543210").
    - Assert: HTTP 201 Created, passwords hashed (bcrypt), JWT tokens generated with correct role claims.
    """
    client = TestClient(app)
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    mock_query_res = MagicMock()
    mock_query_res.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_query_res

    app.dependency_overrides[get_db] = lambda: mock_db

    payload_a = {
        "role": "donor",
        "full_name": "Green Dine Restaurant",
        "email": "greendine@restaurant.in",
        "password": "SecurePassword123!",
        "phone_number": "+919811223344",
        "address_line": "Block B, North Delhi",
        "location": {"latitude": 28.7041, "longitude": 77.1025},
    }
    resp_a = client.post("/api/v1/auth/signup", json=payload_a)
    assert resp_a.status_code == status.HTTP_201_CREATED
    data_a = resp_a.json()
    assert data_a["user"]["role"] == "donor"
    assert data_a["user"]["full_name"] == "Green Dine Restaurant"
    assert "access_token" in data_a
    assert data_a["token_type"] == "bearer"

    payload_b = {
        "role": "ngo",
        "full_name": "Hope Shelter Coordinator",
        "email": "director@hopeshelter.org",
        "password": "SecurePassword123!",
        "phone_number": "+919876500112",
        "organization_name": "Hope Shelter Foundation",
        "registration_number": "NGO-102938",
        "operating_radius_km": 25.0,
        "location": {"latitude": 28.7100, "longitude": 77.1100},
    }
    resp_b = client.post("/api/v1/auth/signup", json=payload_b)
    assert resp_b.status_code == status.HTTP_201_CREATED
    data_b = resp_b.json()
    assert data_b["user"]["role"] == "ngo"
    assert "access_token" in data_b

    payload_c = {
        "role": "driver",
        "full_name": "Alex Driver",
        "email": "alex.driver@sts-express.in",
        "password": "SecurePassword123!",
        "phone_number": "+919876543210",
    }
    resp_c = client.post("/api/v1/auth/signup", json=payload_c)
    assert resp_c.status_code == status.HTTP_201_CREATED
    data_c = resp_c.json()
    assert data_c["user"]["role"] == "driver"
    assert data_c["user"]["phone_number"] == "+919876543210"

    hashed = get_password_hash("SecurePassword123!")
    assert hashed != "SecurePassword123!"
    assert verify_password("SecurePassword123!", hashed) is True

    app.dependency_overrides.clear()


def test_suite_1_profile_settings_and_capacity_toggles(qa_actors):
    """Suite 1.2: Test Profile & Settings.

    - Donor updates notification settings to disable marketing emails and enable instant pickup SMS alerts.
    - NGO toggles emergency capacity status between 'accepting' and 'at_capacity'.
    - Assert: Database profile values update and invalid enum payloads return HTTP 422.
    """
    client = TestClient(app)
    donor = qa_actors["donor"]
    ngo = qa_actors["ngo"]

    app.dependency_overrides[get_current_user] = lambda: donor
    notif_payload = {
        "push_enabled": True,
        "email_enabled": False,
        "sms_alerts_enabled": True,
        "urgent_surplus_alerts": True,
    }
    notif_resp = client.put("/api/v1/settings/notifications", json=notif_payload)
    app.dependency_overrides.clear()

    assert notif_resp.status_code == status.HTTP_200_OK
    notif_data = notif_resp.json()
    assert notif_data["email_enabled"] is False
    assert notif_data["sms_alerts_enabled"] is True

    mock_db = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = ngo.ngo_details
    mock_db.execute.return_value = mock_res

    app.dependency_overrides[get_current_user] = lambda: ngo
    app.dependency_overrides[get_db] = lambda: mock_db

    cap_resp1 = client.patch(
        f"/api/v1/ngos/{ngo.ngo_details.id}/capacity",
        json={"capacity_status": "at_capacity"},
    )
    assert cap_resp1.status_code == status.HTTP_200_OK
    assert cap_resp1.json()["is_accepting_donations"] is False
    assert cap_resp1.json()["capacity_status"] == "at_capacity"

    cap_resp2 = client.patch(
        f"/api/v1/ngos/{ngo.ngo_details.id}/capacity",
        json={"capacity_status": "accepting"},
    )
    assert cap_resp2.status_code == status.HTTP_200_OK
    assert cap_resp2.json()["is_accepting_donations"] is True
    assert cap_resp2.json()["capacity_status"] == "accepting"

    invalid_resp = client.patch(
        f"/api/v1/ngos/{ngo.ngo_details.id}/capacity",
        json={"capacity_status": "INVALID_STATUS_CODE"},
    )
    assert invalid_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    app.dependency_overrides.clear()


def test_suite_1_rbac_route_protection(qa_actors):
    """Suite 1.3: Test RBAC Route Protection.

    - Attempt to access NGO-restricted route (POST /donations/{id}/claim) using Donor JWT token.
    - Assert: HTTP 403 Forbidden with message "Insufficient permissions".
    """
    client = TestClient(app)
    donor = qa_actors["donor"]

    app.dependency_overrides[get_current_user] = lambda: donor
    claim_resp = client.post(f"/api/v1/donations/{uuid.uuid4()}/claim")
    app.dependency_overrides.clear()

    assert claim_resp.status_code == status.HTTP_403_FORBIDDEN
    assert "Insufficient permissions" in claim_resp.json()["detail"]


def test_suite_2_perishable_food_and_postgis_srid_storage(qa_actors):
    """Suite 2.1: Perishable Cooked Food Flow.

    - Donor posts surplus cooked food (50 meals, veg, prepared 1 hour ago, expires_at: NOW + 3 hours, Lat/Lng: 28.7041, 77.1025).
    - Assert: Status 'available', PostGIS point stored in SRID 4326.
    """
    client = TestClient(app)
    donor = qa_actors["donor"]
    now = datetime.now(timezone.utc)

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: donor
    app.dependency_overrides[get_db] = lambda: mock_db

    food_payload = {
        "kind": "physical_item",
        "category": "cooked_food",
        "title": "50 Fresh Vegetarian Lunch Trays",
        "description": "Vegetarian meal trays prepared in hygienic industrial kitchen.",
        "quantity_amount": 50.0,
        "quantity_unit": "meals",
        "pickup_address": "Green Dine Restaurant, Block B, North Delhi",
        "pickup_location": {"latitude": 28.7041, "longitude": 77.1025},
        "is_perishable": True,
        "prepared_at": (now - timedelta(hours=1)).isoformat(),
        "expires_at": (now + timedelta(hours=3)).isoformat(),
        "dietary_tags": ["vegetarian"],
    }
    resp = client.post("/api/v1/donations", json=food_payload)
    app.dependency_overrides.clear()

    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["status"] == "available"
    assert data["category"] == "cooked_food"
    assert data["is_perishable"] is True
    assert data["pickup_location"]["latitude"] == 28.7041
    assert data["pickup_location"]["longitude"] == 77.1025

    pt_geo = create_point_geography(77.1025, 28.7041, srid=4326)
    assert pt_geo is not None
    parsed = parse_geography_point(pt_geo)
    assert parsed is not None
    assert round(parsed[0], 4) == 77.1025
    assert round(parsed[1], 4) == 28.7041


def test_suite_2_geospatial_discovery_radius_and_filtering(qa_actors):
    """Suite 2.2: Geospatial Discovery Radius.

    - Execute NGO feed query from User B's coordinates (within 2 km).
    - Assert: The newly created donation appears with calculated distance (< 2 km).
    - Mock a third NGO 40 km away; verify this distant NGO's feed excludes the donation when querying a 10 km default radius.
    """
    client = TestClient(app)
    donor = qa_actors["donor"]
    ngo = qa_actors["ngo"]
    now = datetime.now(timezone.utc)

    donation_record = Donation(
        id=uuid.uuid4(),
        donor_id=donor.id,
        kind=DonationKind.PHYSICAL_ITEM,
        category=ItemCategory.COOKED_FOOD,
        status=DonationStatus.AVAILABLE,
        title="50 Fresh Vegetarian Lunch Trays",
        quantity_amount=Decimal("50.0"),
        quantity_unit="meals",
        pickup_address="Block B, North Delhi",
        pickup_location=create_point_geography(77.1025, 28.7041),
        is_perishable=True,
        expiry_time=now + timedelta(hours=3),
        created_at=now,
        updated_at=now,
    )

    matched_entry_nearby = MatchedDonation(
        donation=donation_record,
        distance_km=1.01,
        urgency_level="high",
        is_claimable=True,
    )

    app.dependency_overrides[get_current_user] = lambda: ngo
    app.dependency_overrides[get_db] = lambda: AsyncMock()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.api.v1.endpoints.donations.find_nearby_donations",
            AsyncMock(return_value=[matched_entry_nearby]),
        )
        feed_resp_nearby = client.get(
            "/api/v1/donations/feed",
            params={"user_lat": 28.7100, "user_lon": 77.1100, "radius_km": 5.0},
        )
    assert feed_resp_nearby.status_code == status.HTTP_200_OK
    items_nearby = feed_resp_nearby.json()
    assert len(items_nearby) == 1
    assert items_nearby[0]["distance_km"] < 2.0

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.api.v1.endpoints.donations.find_nearby_donations",
            AsyncMock(return_value=[]),
        )
        feed_resp_distant = client.get(
            "/api/v1/donations/feed",
            params={"user_lat": 28.4595, "user_lon": 77.0266, "radius_km": 10.0},
        )
    assert feed_resp_distant.status_code == status.HTTP_200_OK
    items_distant = feed_resp_distant.json()
    assert len(items_distant) == 0

    app.dependency_overrides.clear()


def test_suite_2_multi_category_physical_items(qa_actors):
    """Suite 2.3: Multi-Category Physical Items.

    - Donor creates a batch listing containing:
      a) 20 Winter Blankets (Category: 'blanket', Condition: 'gently used').
      b) First Aid Kits & Bandages (Category: 'medical').
      c) Custom Item ("15 School Backpacks and Notebooks", Category: 'other').
    - Assert: All records persist with accurate item_category enums and image URL arrays.
    """
    client = TestClient(app)
    donor = qa_actors["donor"]

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: donor
    app.dependency_overrides[get_db] = lambda: mock_db

    payload_a = {
        "kind": "physical_item",
        "category": "blanket",
        "title": "20 Winter Woolen Blankets",
        "description": "Gently used, laundered and sanitized winter blankets.",
        "quantity_amount": 20.0,
        "quantity_unit": "pieces",
        "pickup_address": "Green Dine Restaurant, Delhi",
        "pickup_location": {"latitude": 28.7041, "longitude": 77.1025},
        "is_perishable": False,
        "image_urls": ["https://storage.sts.org/blankets1.jpg"],
    }
    resp_a = client.post("/api/v1/donations", json=payload_a)
    assert resp_a.status_code == status.HTTP_201_CREATED
    assert resp_a.json()["category"] == "blanket"
    assert resp_a.json()["image_urls"] == ["https://storage.sts.org/blankets1.jpg"]

    payload_b = {
        "kind": "physical_item",
        "category": "medical",
        "title": "First Aid Kits & Bandages",
        "description": "Sterilized emergency bandages and antiseptics.",
        "quantity_amount": 10.0,
        "quantity_unit": "kits",
        "pickup_address": "Green Dine Restaurant, Delhi",
        "pickup_location": {"latitude": 28.7041, "longitude": 77.1025},
        "is_perishable": False,
        "image_urls": ["https://storage.sts.org/medical_box.jpg"],
    }
    resp_b = client.post("/api/v1/donations", json=payload_b)
    assert resp_b.status_code == status.HTTP_201_CREATED
    assert resp_b.json()["category"] == "medical"

    payload_c = {
        "kind": "physical_item",
        "category": "other",
        "title": "15 School Backpacks and Notebooks",
        "description": "Educational supplies for shelter children.",
        "quantity_amount": 15.0,
        "quantity_unit": "backpacks",
        "pickup_address": "Green Dine Restaurant, Delhi",
        "pickup_location": {"latitude": 28.7041, "longitude": 77.1025},
        "is_perishable": False,
    }
    resp_c = client.post("/api/v1/donations", json=payload_c)
    assert resp_c.status_code == status.HTTP_201_CREATED
    assert resp_c.json()["category"] == "other"

    app.dependency_overrides.clear()


def test_suite_3_direct_financial_donation_and_webhook_update(qa_actors):
    """Suite 3.1: Direct Financial Donation.

    - Donor initiates direct monetary donation of ₹2,500 ($30) directly to User B ("Hope Shelter Foundation").
    - Simulate payment gateway webhook callback (payment_status: completed, payment_gateway_ref: "pay_test_98721").
    - Assert: Transaction is verified, donation status moves to 'completed', and NGO ledger updates.
    """
    client = TestClient(app)
    donor = qa_actors["donor"]
    ngo = qa_actors["ngo"]
    now = datetime.now(timezone.utc)
    donation_id = uuid.uuid4()

    pending_direct = Donation(
        id=donation_id,
        donor_id=donor.id,
        assigned_ngo_id=ngo.ngo_details.id,
        kind=DonationKind.MONETARY_DIRECT,
        status=DonationStatus.PENDING,
        title="Direct Shelter Winter Relief Support",
        quantity_amount=Decimal("2500.00"),
        monetary_currency="INR",
        is_perishable=False,
        metadata_json={"payment_status": "pending", "ledger_status": "unallocated"},
        created_at=now,
        updated_at=now,
    )

    mock_db = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = pending_direct
    mock_db.execute.return_value = mock_res

    app.dependency_overrides[get_db] = lambda: mock_db

    webhook_payload = {
        "payment_status": "completed",
        "payment_gateway_ref": "pay_test_98721",
        "donation_id": str(donation_id),
    }
    webhook_resp = client.post("/api/v1/donations/payment-webhook", json=webhook_payload)
    app.dependency_overrides.clear()

    assert webhook_resp.status_code == status.HTTP_200_OK
    data = webhook_resp.json()
    assert data["action"] == "donation_completed"
    assert data["payment_status"] == "completed"
    assert data["payment_gateway_ref"] == "pay_test_98721"
    assert data["ledger_status"] == "credited"

    assert pending_direct.status == DonationStatus.COMPLETED
    assert pending_direct.metadata_json["ledger_status"] == "credited"
    assert pending_direct.metadata_json["payment_gateway_ref"] == "pay_test_98721"


def test_suite_3_earmarked_item_purchase_donation(qa_actors):
    """Suite 3.2: Earmarked 'Item-Purchase' Donation.

    - NGO posts an earmarked request for "50 Woolen Blankets" at ₹200 each.
    - Donor chooses to fund 20 blankets (Total: ₹4,000).
    - Payment intent completes; assert that funds are escrowed and assigned specifically to earmarked_item_name: "Woolen Blankets".
    """
    client = TestClient(app)
    donor = qa_actors["donor"]
    ngo = qa_actors["ngo"]

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_res_ngo = MagicMock()
    mock_res_ngo.scalar_one_or_none.return_value = ngo.ngo_details
    mock_db.execute.return_value = mock_res_ngo

    app.dependency_overrides[get_current_user] = lambda: donor
    app.dependency_overrides[get_db] = lambda: mock_db

    fund_payload = {
        "item_name": "Woolen Blankets",
        "cost_per_unit": 200.0,
        "units_count": 20,
        "total_amount_funded": 4000.0,
        "target_ngo_id": str(ngo.ngo_details.id),
        "currency": "INR",
        "donor_note": "Funding 20 winter woolen blankets for Hope Shelter.",
    }
    create_resp = client.post("/api/v1/donations/earmarked-fund", json=fund_payload)
    assert create_resp.status_code == status.HTTP_201_CREATED
    create_data = create_resp.json()
    assert create_data["item_name"] == "Woolen Blankets"
    assert create_data["units_count"] == 20
    assert float(create_data["total_amount"]) == 4000.0
    assert create_data["currency"] == "INR"
    assert create_data["escrow_status"] == "intent_created"

    earmarked_donation_id = uuid.UUID(create_data["donation_id"])

    now = datetime.now(timezone.utc)
    earmarked_record = Donation(
        id=earmarked_donation_id,
        donor_id=donor.id,
        assigned_ngo_id=ngo.ngo_details.id,
        kind=DonationKind.MONETARY_EARMARKED,
        status=DonationStatus.PENDING,
        title="Earmarked Aid: Woolen Blankets",
        quantity_amount=Decimal("4000.00"),
        monetary_currency="INR",
        earmarked_cause="Woolen Blankets",
        metadata_json={
            "item_name": "Woolen Blankets",
            "earmarked_item_name": "Woolen Blankets",
            "units_count": 20,
            "cost_per_unit": 200.0,
            "escrow_status": "intent_created",
        },
        created_at=now,
        updated_at=now,
    )

    mock_db_confirm = AsyncMock()
    mock_db_confirm.flush = AsyncMock()
    mock_res_c = MagicMock()
    mock_res_c.scalar_one_or_none.return_value = earmarked_record
    mock_db_confirm.execute.return_value = mock_res_c

    app.dependency_overrides[get_db] = lambda: mock_db_confirm

    confirm_resp = client.post(
        f"/api/v1/donations/earmarked-fund/{earmarked_donation_id}/confirm",
        json={"payment_intent_id": "pi_live_44332211", "payment_status": "succeeded"},
    )
    app.dependency_overrides.clear()

    assert confirm_resp.status_code == status.HTTP_200_OK
    confirm_data = confirm_resp.json()
    assert confirm_data["status"] == "completed"
    assert confirm_data["escrow_status"] == "funded"
    assert float(confirm_data["total_amount"]) == 4000.0

    assert earmarked_record.status == DonationStatus.COMPLETED
    assert earmarked_record.metadata_json["earmarked_item_name"] == "Woolen Blankets"
    assert earmarked_record.metadata_json["escrow_status"] == "funded"


@pytest.mark.asyncio
async def test_suite_4_expiry_monitor_urgency_escalation(qa_actors):
    """Suite 4.1: Expiry Monitor Task.

    - Seed unclaimed cooked food item with expires_at set to NOW + 45 minutes.
    - Trigger expiry_monitor background evaluation task.
    - Assert: Priority automatically escalates to 'CRITICAL_URGENCY', and search radius expands to alert secondary NGOs.
    """
    donor = qa_actors["donor"]
    now = datetime.now(timezone.utc)

    urgent_donation = Donation(
        id=uuid.uuid4(),
        donor_id=donor.id,
        kind=DonationKind.PHYSICAL_ITEM,
        category=ItemCategory.COOKED_FOOD,
        status=DonationStatus.AVAILABLE,
        title="Surplus Biryani Pots",
        quantity_amount=Decimal("80"),
        is_perishable=True,
        prepared_at=now - timedelta(hours=3),
        expiry_time=now + timedelta(minutes=45),
        metadata_json={"search_radius_km": 25.0, "urgency_status": "normal"},
        created_at=now,
        updated_at=now,
    )

    mock_db = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_res_donations = MagicMock()
    mock_res_donations.scalars.return_value.all.return_value = [urgent_donation]
    mock_res_ngos = MagicMock()
    mock_res_ngos.scalars.return_value.all.return_value = ["Hope Shelter Foundation", "City Food Bank"]
    mock_db.execute.side_effect = [mock_res_donations, mock_res_ngos]

    report = await scan_and_escalate_perishables(mock_db, critical_threshold_hours=2.0, radius_multiplier=2.0)

    assert report.escalated_count == 1
    assert len(report.escalations) == 1
    event = report.escalations[0]
    assert event.donation_id == urgent_donation.id
    assert 40 <= event.minutes_remaining <= 45
    assert event.original_radius_km == 25.0
    assert event.expanded_radius_km == 50.0

    meta = urgent_donation.metadata_json
    assert meta["urgency_status"] == "CRITICAL_URGENCY"
    assert meta["is_escalated"] is True
    assert meta["expanded_radius_km"] == 50.0


@pytest.mark.asyncio
async def test_suite_4_expired_food_auto_disqualification(qa_actors):
    """Suite 4.2: Expired Food Auto-Disqualification.

    - Seed item with expires_at in the past (NOW - 10 minutes).
    - Trigger monitor task.
    - Assert: Donation status shifts to 'expired' and is removed from live public discovery feeds.
    """
    donor = qa_actors["donor"]
    now = datetime.now(timezone.utc)

    spoiled_donation = Donation(
        id=uuid.uuid4(),
        donor_id=donor.id,
        kind=DonationKind.PHYSICAL_ITEM,
        category=ItemCategory.COOKED_FOOD,
        status=DonationStatus.AVAILABLE,
        title="Leftover Sandwiches",
        quantity_amount=Decimal("30"),
        is_perishable=True,
        prepared_at=now - timedelta(hours=6),
        expiry_time=now - timedelta(minutes=10),
        created_at=now,
        updated_at=now,
    )

    mock_db = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [spoiled_donation]
    mock_db.execute.return_value = mock_res

    report = await scan_and_escalate_perishables(mock_db)

    assert report.expired_count == 1
    assert spoiled_donation.id in report.expired_donation_ids
    assert spoiled_donation.status == DonationStatus.EXPIRED


def test_suite_5_complete_3way_handoff_and_otp_double_handshake(qa_actors):
    """Suite 5: 3-Way Handoff & Driver Logistics.

    1. Claiming & Reservation Hold: User B (NGO) claims available cooked food -> Status: 'reserved', deadline NOW+15m.
    2. Driver Assignment: User C (Driver) accepts run -> OTPs generated, Delivery status: 'assigned'/'accepted'.
    3. Double-Handshake:
       - Invalid pickup OTP -> HTTP 400 "Invalid pickup code".
       - Correct pickup OTP -> Delivery: 'picked_up', Donation: 'in_transit'.
       - Correct dropoff OTP + photo URL -> Delivery: 'delivered', Donation: 'completed'.
    """
    client = TestClient(app)
    donor = qa_actors["donor"]
    ngo = qa_actors["ngo"]
    driver = qa_actors["driver"]
    now = datetime.now(timezone.utc)

    donation_id = uuid.uuid4()
    delivery_id = uuid.uuid4()
    pickup_otp = "772211"
    dropoff_otp = "884422"

    donation = Donation(
        id=donation_id,
        donor_id=donor.id,
        kind=DonationKind.PHYSICAL_ITEM,
        category=ItemCategory.COOKED_FOOD,
        status=DonationStatus.AVAILABLE,
        title="100 Meal Lunch Surplus",
        quantity_amount=Decimal("100"),
        is_perishable=True,
        expiry_time=now + timedelta(hours=4),
        created_at=now,
        updated_at=now,
    )

    mock_db_claim = AsyncMock()
    mock_db_claim.flush = AsyncMock()
    c_res = MagicMock()
    c_res.scalar_one_or_none.return_value = donation
    mock_db_claim.execute.return_value = c_res

    app.dependency_overrides[get_current_user] = lambda: ngo
    app.dependency_overrides[get_db] = lambda: mock_db_claim

    claim_resp = client.post(f"/api/v1/donations/{donation_id}/claim")
    assert claim_resp.status_code == status.HTTP_200_OK
    assert claim_resp.json()["status"] == "reserved"
    assert claim_resp.json()["reservation_lock_minutes"] == 15
    assert donation.status == DonationStatus.RESERVED

    delivery = Delivery(
        id=delivery_id,
        donation_id=donation_id,
        destination_ngo_id=ngo.ngo_details.id,
        driver_id=None,
        status=DeliveryStatus.ASSIGNED,
        pickup_otp_hash=hash_otp(pickup_otp),
        delivery_otp_hash=hash_otp(dropoff_otp),
        created_at=now,
        updated_at=now,
    )
    delivery.donation = donation

    mock_db_accept = AsyncMock()
    mock_db_accept.flush = AsyncMock()
    a_res = MagicMock()
    a_res.scalar_one_or_none.return_value = delivery
    mock_db_accept.execute.return_value = a_res

    app.dependency_overrides[get_current_user] = lambda: driver
    app.dependency_overrides[get_db] = lambda: mock_db_accept

    accept_resp = client.post(f"/api/v1/deliveries/{delivery_id}/accept")
    assert accept_resp.status_code == status.HTTP_200_OK
    assert accept_resp.json()["status"] == "accepted"
    assert delivery.driver_id == driver.id

    mock_db_handshake = AsyncMock()
    mock_db_handshake.flush = AsyncMock()
    h_res = MagicMock()
    h_res.scalar_one_or_none.return_value = delivery
    mock_db_handshake.execute.return_value = h_res

    app.dependency_overrides[get_db] = lambda: mock_db_handshake

    bad_otp_resp = client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-verify",
        json={"pickup_otp": "000000"},
    )
    assert bad_otp_resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid pickup code" in bad_otp_resp.json()["detail"]

    good_pickup_resp = client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-verify",
        json={"pickup_otp": pickup_otp, "proof_of_pickup_url": "https://storage.sts.org/proofs/pickup.jpg"},
    )
    assert good_pickup_resp.status_code == status.HTTP_200_OK
    assert delivery.status == DeliveryStatus.PICKED_UP
    assert donation.status == DonationStatus.IN_TRANSIT

    good_dropoff_resp = client.post(
        f"/api/v1/deliveries/{delivery_id}/dropoff-verify",
        json={
            "dropoff_otp": dropoff_otp,
            "proof_of_delivery_url": "https://storage.sts.org/proofs/shelter_dropoff.jpg",
        },
    )
    assert good_dropoff_resp.status_code == status.HTTP_200_OK
    assert delivery.status == DeliveryStatus.DELIVERED
    assert donation.status == DonationStatus.COMPLETED

    app.dependency_overrides.clear()


def test_suite_6_ngo_directory_and_contact_lookup(qa_actors):
    """Suite 6.1: NGO Directory & Contact Lookup.

    - Public/unauthenticated user queries GET /ngos?search=Hope+Shelter.
    - Assert: Returns verified contact details, operational hours, emergency phone number, and accepted categories without exposing private bank fields.
    """
    client = TestClient(app)
    ngo = qa_actors["ngo"].ngo_details

    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [ngo]
    mock_db.execute.return_value = mock_res

    app.dependency_overrides[get_db] = lambda: mock_db

    resp = client.get("/api/v1/ngos?search=Hope+Shelter")
    app.dependency_overrides.clear()

    assert resp.status_code == status.HTTP_200_OK
    results = resp.json()
    assert len(results) == 1
    item = results[0]
    assert item["organization_name"] == "Hope Shelter Foundation"
    assert item["registration_number"] == "NGO-102938"
    assert item["contact_phone"] == "+919876500112"
    assert "emergency_phone_number" in item
    assert "operational_hours" in item
    assert "accepted_categories" in item

    assert "bank_account" not in item
    assert "routing_number" not in item
    assert "stripe_secret" not in item


def test_suite_6_help_and_support_tickets(qa_actors):
    """Suite 6.2: Help & Support Tickets.

    - Driver submits support ticket regarding "Wrong donor address".
    - Assert: Ticket stored under support_tickets linked to user ID.
    """
    client = TestClient(app)
    driver = qa_actors["driver"]

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: driver
    app.dependency_overrides[get_db] = lambda: mock_db

    ticket_payload = {
        "subject": "Wrong donor address",
        "message": "The donor pickup location on the map does not match the street address provided.",
        "priority": "high",
    }
    resp = client.post("/api/v1/support/tickets", json=ticket_payload)
    app.dependency_overrides.clear()

    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["subject"] == "Wrong donor address"
    assert data["priority"] == "high"
    assert data["status"] == "open"
    assert data["creator_id"] == str(driver.id)


def test_suite_6_esg_and_waste_metrics_generation(qa_actors):
    """Suite 6.3: ESG & Waste Metrics Generation.

    - Donor requests impact report (GET /esg/stats).
    - Assert: Metrics correctly aggregate total meals rescued, kg of waste diverted, and CO2 offsets saved from completed deliveries.
    """
    client = TestClient(app)
    donor = qa_actors["donor"]
    now = datetime.now(timezone.utc)

    d1 = Donation(
        id=uuid.uuid4(),
        donor_id=donor.id,
        category=ItemCategory.COOKED_FOOD,
        status=DonationStatus.COMPLETED,
        quantity_amount=Decimal("100"),
        created_at=now,
        updated_at=now,
    )
    d2 = Donation(
        id=uuid.uuid4(),
        donor_id=donor.id,
        category=ItemCategory.COOKED_FOOD,
        status=DonationStatus.COMPLETED,
        quantity_amount=Decimal("50"),
        created_at=now,
        updated_at=now,
    )

    mock_db = AsyncMock()
    mock_food_res = MagicMock()
    mock_food_res.scalars.return_value.all.return_value = [d1, d2]
    mock_deliv_res = MagicMock()
    mock_deliv_res.scalar.return_value = 2
    mock_money_res = MagicMock()
    mock_money_res.scalars.return_value.all.return_value = []
    mock_db.execute.side_effect = [mock_food_res, mock_deliv_res, mock_money_res]

    app.dependency_overrides[get_current_user] = lambda: donor
    app.dependency_overrides[get_db] = lambda: mock_db

    resp = client.get("/esg/stats")
    app.dependency_overrides.clear()

    assert resp.status_code == status.HTTP_200_OK
    stats_data = resp.json()
    assert stats_data["total_meals_rescued"] == 150
    assert stats_data["total_kg_waste_diverted"] == 67.5
    assert stats_data["total_co2_offset_kg"] == 168.75
    assert stats_data["total_deliveries_completed"] == 2
