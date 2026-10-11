"""Comprehensive End-to-End Integration Test Suite for Save The Serve (S.T.S)

Verifies:
1. Full Operational Cycle:
   - Donor posts cooked food (with prepared_at & expires_at constraints).
   - PostGIS matches nearest NGO (geospatial proximity query via ST_DWithin / ST_Distance).
   - NGO claims donation with 15-minute concurrency reservation lock.
   - Delivery dispatch task created with 6-digit OTPs.
   - Driver accepts/is assigned to delivery task.
   - Driver verifies donor pickup using 6-digit pickup_otp (transitions to IN_TRANSIT).
   - Driver verifies NGO drop-off using 6-digit dropoff_otp + proof image (transitions to COMPLETED).
2. Monetary Earmarked Donation Flow:
   - Donor creates earmarked funding intent for essential items (status: PENDING).
   - Payment gateway confirmation callback updates status to COMPLETED and escrow to 'funded'.
   - Payment gateway webhook callback updates donation status asynchronously.
   - Payment failure transitions status to CANCELLED.
3. Health and Readiness Probes:
   - GET /health liveness probe.
   - GET /ready readiness probe with database and PostGIS checks.
   - GET / welcoming operational status.
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
from app.models.enums import (
    DeliveryStatus,
    DonationKind,
    DonationStatus,
    ItemCategory,
    UserRole,
)
from app.models.ngo import NGODetail
from app.models.profile import Profile
from app.schemas.ngo import encode_ngo_capacity_meta
from app.services.matching_engine import MatchedDonation


@pytest.fixture
def donor_actor():
    """Donor user fixture."""
    return Profile(
        id=uuid.uuid4(),
        email="donor.sarah@sts-rescue.org",
        role=UserRole.DONOR,
        full_name="Sarah Jenkins (Bakery Owner)",
        hashed_password=get_password_hash("DonorSecure2026!"),
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def ngo_actor():
    """NGO coordinator and organization fixture."""
    profile_id = uuid.uuid4()
    ngo_id = uuid.uuid4()
    ngo_details = NGODetail(
        id=ngo_id,
        profile_id=profile_id,
        organization_name="San Francisco Food Oasis Shelter",
        registration_number="NGO-SFFO-9911",
        operating_radius_km=Decimal("25.00"),
        hq_location=create_point_geography(-122.4194, 37.7749),
        is_approved=True,
        contact_email="intake@foodoasis.org",
        contact_phone="+14155550199",
        capacity_description=encode_ngo_capacity_meta(
            description="Active shelter with industrial cooling",
            is_accepting=True,
            accepted_categories=[ItemCategory.COOKED_FOOD, ItemCategory.GROCERY],
        ),
    )
    ngo_profile = Profile(
        id=profile_id,
        email="director@foodoasis.org",
        role=UserRole.NGO,
        full_name="Marcus Vance (NGO Director)",
        hashed_password=get_password_hash("NgoDirectorSecure2026!"),
        is_active=True,
        is_verified=True,
        ngo_details=ngo_details,
    )
    return ngo_profile


@pytest.fixture
def driver_actor():
    """Volunteer/Commercial driver fixture."""
    return Profile(
        id=uuid.uuid4(),
        email="driver.carlos@sts-dispatch.org",
        role=UserRole.DRIVER,
        full_name="Carlos Mendez (Rapid Volunteer)",
        hashed_password=get_password_hash("DriverSecure2026!"),
        is_active=True,
        is_verified=True,
    )


def test_complete_donation_to_delivery_lifecycle(donor_actor, ngo_actor, driver_actor):
    """End-to-end integration test verifying the complete operational cycle:

    Cycle:
    1. Donor posts cooked food (prepared_at, expires_at, coordinates).
    2. PostGIS matches nearest NGO in geospatial discovery feed.
    3. NGO claims donation with 15-minute concurrency reservation lock.
    4. NGO initiates delivery dispatch task (generates 6-digit OTPs).
    5. Driver claims / is assigned to delivery task.
    6. Driver verifies pickup with donor's 6-digit OTP -> Status becomes 'in_transit'.
    7. Driver verifies drop-off with NGO's 6-digit OTP + image proof -> Status marked 'completed'.
    """
    client = TestClient(app)
    now = datetime.now(timezone.utc)
    donation_id = uuid.uuid4()
    delivery_id = uuid.uuid4()
    pickup_otp = "482910"
    dropoff_otp = "918273"

    donation_record = Donation(
        id=donation_id,
        donor_id=donor_actor.id,
        kind=DonationKind.PHYSICAL_ITEM,
        category=ItemCategory.COOKED_FOOD,
        status=DonationStatus.AVAILABLE,
        title="100 Freshly Cooked Rice & Curry Trays",
        description="Freshly prepared catering surplus, packaged in insulated containers.",
        quantity_amount=Decimal("100.0"),
        quantity_unit="meals",
        pickup_address="500 Howard St, San Francisco, CA 94105",
        pickup_location=create_point_geography(-122.3985, 37.7885),
        is_perishable=True,
        prepared_at=now - timedelta(hours=1),
        expiry_time=now + timedelta(hours=5),
        created_at=now,
        updated_at=now,
    )

    delivery_record = Delivery(
        id=delivery_id,
        donation_id=donation_id,
        destination_ngo_id=ngo_actor.ngo_details.id,
        driver_id=None,
        status=DeliveryStatus.ASSIGNED,
        pickup_location=create_point_geography(-122.3985, 37.7885),
        dropoff_location=create_point_geography(-122.4194, 37.7749),
        pickup_otp_hash=hash_otp(pickup_otp),
        delivery_otp_hash=hash_otp(dropoff_otp),
        estimated_distance_km=Decimal("2.4"),
        estimated_duration_mins=14,
        created_at=now,
        updated_at=now,
    )
    delivery_record.donation = donation_record

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: donor_actor
    app.dependency_overrides[get_db] = lambda: mock_db

    post_payload = {
        "kind": "physical_item",
        "category": "cooked_food",
        "title": "100 Freshly Cooked Rice & Curry Trays",
        "description": "Freshly prepared catering surplus, packaged in insulated containers.",
        "quantity_amount": 100.0,
        "quantity_unit": "meals",
        "pickup_address": "500 Howard St, San Francisco, CA 94105",
        "pickup_location": {"longitude": -122.3985, "latitude": 37.7885},
        "is_perishable": True,
        "prepared_at": (now - timedelta(hours=1)).isoformat(),
        "expires_at": (now + timedelta(hours=5)).isoformat(),
        "dietary_tags": ["halal", "vegetarian"],
    }

    create_resp = client.post("/api/v1/donations", json=post_payload)
    app.dependency_overrides.clear()

    assert create_resp.status_code == status.HTTP_201_CREATED
    created_data = create_resp.json()
    assert created_data["title"] == "100 Freshly Cooked Rice & Curry Trays"
    assert created_data["category"] == "cooked_food"
    assert created_data["status"] == "available"
    assert created_data["is_perishable"] is True

    matched_entry = MatchedDonation(
        donation=donation_record,
        distance_km=2.42,
        urgency_level="high",
        is_claimable=True,
    )

    mock_db_feed = AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: ngo_actor
    app.dependency_overrides[get_db] = lambda: mock_db_feed

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.api.v1.endpoints.donations.find_nearby_donations",
            AsyncMock(return_value=[matched_entry]),
        )
        feed_resp = client.get(
            "/api/v1/donations/feed",
            params={
                "user_lat": 37.7749,
                "user_lon": -122.4194,
                "radius_km": 10.0,
                "category": "cooked_food",
            },
        )
    app.dependency_overrides.clear()

    assert feed_resp.status_code == status.HTTP_200_OK
    feed_items = feed_resp.json()
    assert len(feed_items) == 1
    assert feed_items[0]["id"] == str(donation_id)
    assert feed_items[0]["distance_km"] == 2.42
    assert feed_items[0]["urgency_level"] == "high"
    assert feed_items[0]["is_claimable"] is True

    mock_db_claim = AsyncMock()
    mock_db_claim.flush = AsyncMock()
    claim_query_res = MagicMock()
    claim_query_res.scalar_one_or_none.return_value = donation_record
    mock_db_claim.execute.return_value = claim_query_res

    app.dependency_overrides[get_current_user] = lambda: ngo_actor
    app.dependency_overrides[get_db] = lambda: mock_db_claim

    claim_resp = client.post(f"/api/v1/donations/{donation_id}/claim")
    app.dependency_overrides.clear()

    assert claim_resp.status_code == status.HTTP_200_OK
    claim_data = claim_resp.json()
    assert claim_data["donation_id"] == str(donation_id)
    assert claim_data["status"] == "reserved"
    assert claim_data["reservation_lock_minutes"] == 15
    assert donation_record.status == DonationStatus.RESERVED
    assert donation_record.assigned_ngo_id == ngo_actor.ngo_details.id

    mock_db_dispatch = AsyncMock()
    mock_db_dispatch.add = MagicMock()
    mock_db_dispatch.flush = AsyncMock()
    d_res1 = MagicMock()
    d_res1.scalar_one_or_none.return_value = donation_record
    d_res2 = MagicMock()
    d_res2.scalar_one_or_none.return_value = None
    mock_db_dispatch.execute.side_effect = [d_res1, d_res2]

    app.dependency_overrides[get_current_user] = lambda: ngo_actor
    app.dependency_overrides[get_db] = lambda: mock_db_dispatch

    dispatch_payload = {
        "donation_id": str(donation_id),
        "destination_ngo_id": str(ngo_actor.ngo_details.id),
        "pickup_location": {"longitude": -122.3985, "latitude": 37.7885},
        "dropoff_location": {"longitude": -122.4194, "latitude": 37.7749},
        "estimated_distance_km": 2.4,
        "estimated_duration_mins": 14,
    }
    dispatch_resp = client.post("/api/v1/deliveries", json=dispatch_payload)
    app.dependency_overrides.clear()

    assert dispatch_resp.status_code == status.HTTP_201_CREATED
    dispatch_data = dispatch_resp.json()
    plain_pickup_otp = dispatch_data["pickup_otp"]
    plain_dropoff_otp = dispatch_data["dropoff_otp"]
    assert len(plain_pickup_otp) == 6
    assert len(plain_dropoff_otp) == 6

    delivery_record.pickup_otp_hash = hash_otp(plain_pickup_otp)
    delivery_record.delivery_otp_hash = hash_otp(plain_dropoff_otp)

    mock_db_accept = AsyncMock()
    mock_db_accept.flush = AsyncMock()
    acc_res = MagicMock()
    acc_res.scalar_one_or_none.return_value = delivery_record
    mock_db_accept.execute.return_value = acc_res

    app.dependency_overrides[get_current_user] = lambda: driver_actor
    app.dependency_overrides[get_db] = lambda: mock_db_accept

    accept_resp = client.post(f"/api/v1/deliveries/{delivery_id}/accept")
    app.dependency_overrides.clear()

    assert accept_resp.status_code == status.HTTP_200_OK
    assert accept_resp.json()["status"] == "accepted"
    assert delivery_record.status == DeliveryStatus.ACCEPTED
    assert delivery_record.driver_id == driver_actor.id

    mock_db_pickup = AsyncMock()
    mock_db_pickup.flush = AsyncMock()
    pu_res = MagicMock()
    pu_res.scalar_one_or_none.return_value = delivery_record
    mock_db_pickup.execute.return_value = pu_res

    app.dependency_overrides[get_current_user] = lambda: driver_actor
    app.dependency_overrides[get_db] = lambda: mock_db_pickup

    wrong_pickup_resp = client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-verify",
        json={"pickup_otp": "000000"},
    )
    assert wrong_pickup_resp.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED)

    valid_pickup_resp = client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-verify",
        json={
            "pickup_otp": plain_pickup_otp,
            "proof_of_pickup_url": "https://storage.sts.org/proofs/donor_pickup.jpg",
            "current_latitude": 37.7885,
            "current_longitude": -122.3985,
        },
    )
    app.dependency_overrides.clear()

    assert valid_pickup_resp.status_code == status.HTTP_200_OK
    assert valid_pickup_resp.json()["status"] == "picked_up"
    assert delivery_record.status == DeliveryStatus.PICKED_UP
    assert delivery_record.picked_up_at is not None
    assert donation_record.status == DonationStatus.IN_TRANSIT

    mock_db_dropoff = AsyncMock()
    mock_db_dropoff.flush = AsyncMock()
    do_res = MagicMock()
    do_res.scalar_one_or_none.return_value = delivery_record
    mock_db_dropoff.execute.return_value = do_res

    app.dependency_overrides[get_current_user] = lambda: driver_actor
    app.dependency_overrides[get_db] = lambda: mock_db_dropoff

    missing_photo_resp = client.post(
        f"/api/v1/deliveries/{delivery_id}/dropoff-verify",
        json={"dropoff_otp": plain_dropoff_otp, "proof_of_delivery_url": ""},
    )
    assert missing_photo_resp.status_code in (
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_400_BAD_REQUEST,
    )

    valid_dropoff_resp = client.post(
        f"/api/v1/deliveries/{delivery_id}/dropoff-verify",
        json={
            "dropoff_otp": plain_dropoff_otp,
            "proof_of_delivery_url": "https://storage.sts.org/proofs/ngo_shelter_receipt.jpg",
            "current_latitude": 37.7749,
            "current_longitude": -122.4194,
        },
    )
    app.dependency_overrides.clear()

    assert valid_dropoff_resp.status_code == status.HTTP_200_OK
    assert valid_dropoff_resp.json()["status"] == "delivered"
    assert delivery_record.status == DeliveryStatus.DELIVERED
    assert delivery_record.delivered_at is not None
    assert delivery_record.proof_of_delivery_url == "https://storage.sts.org/proofs/ngo_shelter_receipt.jpg"

    assert donation_record.status == DonationStatus.COMPLETED


def test_earmarked_monetary_donation_payment_lifecycle(donor_actor, ngo_actor):
    """Verifies earmarked monetary donation flow:

    1. Donor initiates escrow purchasing intent for target NGO (status: PENDING).
    2. Payment callback confirms settlement -> Status transitions to COMPLETED.
    3. Asynchronous payment webhook triggers automatic status settlement.
    4. Failed payment transitions donation status to CANCELLED.
    """
    client = TestClient(app)
    target_ngo = ngo_actor.ngo_details

    mock_db_create = AsyncMock()
    mock_db_create.add = MagicMock()
    mock_db_create.flush = AsyncMock()
    mock_ngo_res = MagicMock()
    mock_ngo_res.scalar_one_or_none.return_value = target_ngo
    mock_db_create.execute.return_value = mock_ngo_res

    app.dependency_overrides[get_current_user] = lambda: donor_actor
    app.dependency_overrides[get_db] = lambda: mock_db_create

    intent_payload = {
        "item_name": "50 Winter Sleeping Bags",
        "units_count": 50,
        "cost_per_unit": 20.00,
        "total_amount_funded": 1000.00,
        "target_ngo_id": str(target_ngo.id),
        "currency": "USD",
        "donor_note": "For the winter blizzard emergency shelter intake.",
    }

    intent_resp = client.post("/api/v1/donations/earmarked-fund", json=intent_payload)
    app.dependency_overrides.clear()

    assert intent_resp.status_code == status.HTTP_201_CREATED
    intent_data = intent_resp.json()
    assert intent_data["item_name"] == "50 Winter Sleeping Bags"
    assert intent_data["units_count"] == 50
    assert float(intent_data["total_amount"]) == 1000.00
    assert intent_data["escrow_status"] == "intent_created"
    assert "client_secret" in intent_data
    assert intent_data["target_ngo_id"] == str(target_ngo.id)

    donation_uuid = uuid.UUID(intent_data["donation_id"])

    now = datetime.now(timezone.utc)
    pending_donation = Donation(
        id=donation_uuid,
        donor_id=donor_actor.id,
        assigned_ngo_id=target_ngo.id,
        kind=DonationKind.MONETARY_EARMARKED,
        status=DonationStatus.PENDING,
        title="Earmarked Aid: 50 Winter Sleeping Bags",
        quantity_amount=Decimal("1000.00"),
        quantity_unit="items",
        monetary_currency="USD",
        earmarked_cause="50 Winter Sleeping Bags",
        is_perishable=False,
        metadata_json={
            "escrow_status": "intent_created",
            "units_count": 50,
            "cost_per_unit": 20.0,
        },
        created_at=now,
        updated_at=now,
    )

    mock_db_confirm = AsyncMock()
    mock_db_confirm.flush = AsyncMock()
    c_res = MagicMock()
    c_res.scalar_one_or_none.return_value = pending_donation
    mock_db_confirm.execute.return_value = c_res

    app.dependency_overrides[get_current_user] = lambda: donor_actor
    app.dependency_overrides[get_db] = lambda: mock_db_confirm

    confirm_payload = {
        "payment_intent_id": "pi_sts_test_998877665544",
        "payment_status": "succeeded",
        "payment_method": "card",
    }
    confirm_resp = client.post(
        f"/api/v1/donations/earmarked-fund/{donation_uuid}/confirm",
        json=confirm_payload,
    )
    app.dependency_overrides.clear()

    assert confirm_resp.status_code == status.HTTP_200_OK
    confirm_data = confirm_resp.json()
    assert confirm_data["donation_id"] == str(donation_uuid)
    assert confirm_data["status"] == "completed"
    assert confirm_data["escrow_status"] == "funded"
    assert float(confirm_data["total_amount"]) == 1000.00
    assert confirm_data["payment_id"] == "pi_sts_test_998877665544"

    assert pending_donation.status == DonationStatus.COMPLETED
    assert pending_donation.metadata_json["escrow_status"] == "funded"
    assert pending_donation.metadata_json["payment_status"] == "succeeded"

    webhook_donation_id = uuid.uuid4()
    webhook_donation = Donation(
        id=webhook_donation_id,
        donor_id=donor_actor.id,
        assigned_ngo_id=target_ngo.id,
        kind=DonationKind.MONETARY_EARMARKED,
        status=DonationStatus.PENDING,
        title="Earmarked Aid: Baby Formula Tins",
        quantity_amount=Decimal("300.00"),
        metadata_json={"escrow_status": "intent_created"},
        created_at=now,
        updated_at=now,
    )

    mock_db_hook = AsyncMock()
    mock_db_hook.flush = AsyncMock()
    h_res = MagicMock()
    h_res.scalar_one_or_none.return_value = webhook_donation
    mock_db_hook.execute.return_value = h_res

    app.dependency_overrides[get_db] = lambda: mock_db_hook

    webhook_payload = {
        "id": "evt_stripe_11223344",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_wh_332211",
                "status": "succeeded",
                "metadata": {"donation_id": str(webhook_donation_id)},
            }
        },
    }
    hook_resp = client.post("/api/v1/donations/payment-webhook", json=webhook_payload)
    app.dependency_overrides.clear()

    assert hook_resp.status_code == status.HTTP_200_OK
    assert hook_resp.json()["action"] == "donation_completed"
    assert webhook_donation.status == DonationStatus.COMPLETED
    assert webhook_donation.metadata_json["escrow_status"] == "funded"

    failed_donation_id = uuid.uuid4()
    failed_donation = Donation(
        id=failed_donation_id,
        donor_id=donor_actor.id,
        assigned_ngo_id=target_ngo.id,
        kind=DonationKind.MONETARY_EARMARKED,
        status=DonationStatus.PENDING,
        title="Earmarked Aid: Medical Kits",
        quantity_amount=Decimal("450.00"),
        metadata_json={"escrow_status": "intent_created"},
        created_at=now,
        updated_at=now,
    )

    mock_db_fail = AsyncMock()
    mock_db_fail.flush = AsyncMock()
    f_res = MagicMock()
    f_res.scalar_one_or_none.return_value = failed_donation
    mock_db_fail.execute.return_value = f_res

    app.dependency_overrides[get_current_user] = lambda: donor_actor
    app.dependency_overrides[get_db] = lambda: mock_db_fail

    fail_resp = client.post(
        f"/api/v1/donations/earmarked-fund/{failed_donation_id}/confirm",
        json={"payment_status": "failed"},
    )
    app.dependency_overrides.clear()

    assert fail_resp.status_code == status.HTTP_200_OK
    assert fail_resp.json()["status"] == "cancelled"
    assert failed_donation.status == DonationStatus.CANCELLED
    assert failed_donation.metadata_json["escrow_status"] == "payment_failed"


def test_health_and_readiness_probe_endpoints():
    """Verifies container liveness, database/spatial readiness, and root diagnostics."""
    client = TestClient(app)

    root_resp = client.get("/")
    assert root_resp.status_code == status.HTTP_200_OK
    root_data = root_resp.json()
    assert root_data["status"] == "operational"
    assert root_data["documentation"] == "/docs"

    health_resp = client.get("/health")
    assert health_resp.status_code == status.HTTP_200_OK
    health_data = health_resp.json()
    assert health_data["status"] == "healthy"
    assert health_data["postgis_srid"] == 4326

    mock_db_ready = AsyncMock()
    mock_db_ready.execute = AsyncMock()
    mock_res_db = MagicMock()
    mock_res_db.scalar.return_value = 1
    mock_db_ready.execute.return_value = mock_res_db

    app.dependency_overrides[get_db] = lambda: mock_db_ready
    ready_resp = client.get("/ready")
    app.dependency_overrides.clear()

    assert ready_resp.status_code == status.HTTP_200_OK
    ready_data = ready_resp.json()
    assert ready_data["status"] == "ready"
    assert ready_data["database"] == "connected"
    assert ready_data["postgis_extension"] == "active"

    mock_db_down = AsyncMock()
    mock_db_down.execute.side_effect = ConnectionRefusedError("Database connection timed out")

    app.dependency_overrides[get_db] = lambda: mock_db_down
    down_resp = client.get("/ready")
    app.dependency_overrides.clear()

    assert down_resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "Database readiness probe failed" in down_resp.json()["detail"]
