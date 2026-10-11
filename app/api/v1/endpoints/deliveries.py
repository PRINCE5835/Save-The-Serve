"""Delivery Logistics & Verification Handshake Endpoints for Save The Serve (S.T.S)

Implements:
1. POST /deliveries: NGO/Admin dispatches delivery for a reserved donation (generates 6-digit OTPs).
2. GET /deliveries: Feed of assigned/open deliveries for drivers and NGOs.
3. GET /deliveries/{id}: Detailed delivery inspection.
4. POST /deliveries/{id}/accept: Driver claims an assigned delivery task.
5. POST /deliveries/{id}/pickup-verify: Donor pickup handshake using 6-digit OTP.
6. POST /deliveries/{id}/dropoff-verify: NGO drop-off handshake using 6-digit OTP + image proof.
7. PATCH /deliveries/{id}/location: Driver live GPS location updates.
"""

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db, require_any_role, require_role
from app.core.config import settings
from app.core.database import create_point_geography, parse_geography_point
from app.models.delivery import Delivery
from app.models.donation import Donation
from app.models.enums import DeliveryStatus, DonationStatus, UserRole
from app.models.ngo import NGODetail
from app.models.profile import Profile
from app.schemas.delivery import (
    AcceptDeliveryResponse,
    DeliveryCreate,
    DeliveryCreateResponse,
    DeliveryResponse,
    DriverLocationUpdate,
    VerifyDropoffRequest,
    VerifyDropoffResponse,
    VerifyPickupRequest,
    VerifyPickupResponse,
)
from app.schemas.profile import CoordinateSchema

router = APIRouter()


def generate_6digit_otp() -> str:
    """Generates a secure cryptographically random 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000}"


def hash_otp(otp: str) -> str:
    """Creates a salted SHA-256 hash of a 6-digit OTP."""
    salt = settings.JWT_SECRET_KEY[:32]
    return hashlib.sha256(f"{salt}:{otp.strip()}".encode("utf-8")).hexdigest()


def verify_otp(provided_otp: str, stored_hash: Optional[str]) -> bool:
    """Constant-time verification of a 6-digit OTP against its stored hash."""
    if not stored_hash or not provided_otp:
        return False
    calculated = hash_otp(provided_otp)
    return hmac.compare_digest(calculated, stored_hash)


def _format_delivery_response(delivery: Delivery) -> DeliveryResponse:
    """Formats ORM Delivery into validated DeliveryResponse."""
    pickup_coords: Optional[CoordinateSchema] = None
    dropoff_coords: Optional[CoordinateSchema] = None
    driver_coords: Optional[CoordinateSchema] = None

    if delivery.pickup_location is not None:
        pt = parse_geography_point(delivery.pickup_location)
        if pt:
            pickup_coords = CoordinateSchema(longitude=pt[0], latitude=pt[1])

    if delivery.dropoff_location is not None:
        pt = parse_geography_point(delivery.dropoff_location)
        if pt:
            dropoff_coords = CoordinateSchema(longitude=pt[0], latitude=pt[1])

    if delivery.current_driver_location is not None:
        pt = parse_geography_point(delivery.current_driver_location)
        if pt:
            driver_coords = CoordinateSchema(longitude=pt[0], latitude=pt[1])

    now_dt = datetime.now(timezone.utc)
    return DeliveryResponse(
        id=delivery.id,
        donation_id=delivery.donation_id,
        destination_ngo_id=delivery.destination_ngo_id,
        driver_id=delivery.driver_id,
        status=delivery.status,
        pickup_location=pickup_coords,
        dropoff_location=dropoff_coords,
        current_driver_location=driver_coords,
        estimated_distance_km=delivery.estimated_distance_km,
        estimated_duration_mins=delivery.estimated_duration_mins,
        picked_up_at=delivery.picked_up_at,
        delivered_at=delivery.delivered_at,
        proof_of_pickup_url=delivery.proof_of_pickup_url,
        proof_of_delivery_url=delivery.proof_of_delivery_url,
        created_at=delivery.created_at or now_dt,
        updated_at=delivery.updated_at or now_dt,
    )


@router.post(
    "",
    response_model=DeliveryCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Delivery Task",
    description="NGO or Admin initiates delivery dispatch for a donation, generating 6-digit OTPs for donor and recipient NGO.",
)
async def create_delivery(
    payload: DeliveryCreate,
    current_user: Profile = Depends(require_any_role([UserRole.NGO, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> DeliveryCreateResponse:
    """Creates a new Delivery pipeline record with cryptographically hashed OTPs."""
    donation_query = select(Donation).where(Donation.id == payload.donation_id)
    donation = (await db.execute(donation_query)).scalar_one_or_none()
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donation with ID '{payload.donation_id}' does not exist.",
        )

    existing_query = select(Delivery).where(Delivery.donation_id == payload.donation_id)
    existing = (await db.execute(existing_query)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A delivery assignment already exists for this donation.",
        )

    pickup_otp_plain = generate_6digit_otp()
    dropoff_otp_plain = generate_6digit_otp()

    pickup_geo = create_point_geography(
        longitude=payload.pickup_location.longitude,
        latitude=payload.pickup_location.latitude,
        srid=settings.POSTGIS_SRID,
    )
    dropoff_geo = create_point_geography(
        longitude=payload.dropoff_location.longitude,
        latitude=payload.dropoff_location.latitude,
        srid=settings.POSTGIS_SRID,
    )

    delivery_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    delivery = Delivery(
        id=delivery_id,
        donation_id=payload.donation_id,
        destination_ngo_id=payload.destination_ngo_id,
        status=DeliveryStatus.ASSIGNED,
        pickup_location=pickup_geo,
        dropoff_location=dropoff_geo,
        pickup_otp_hash=hash_otp(pickup_otp_plain),
        delivery_otp_hash=hash_otp(dropoff_otp_plain),
        estimated_distance_km=payload.estimated_distance_km,
        estimated_duration_mins=payload.estimated_duration_mins,
        created_at=now,
        updated_at=now,
    )
    db.add(delivery)

    if donation.assigned_ngo_id is None:
        donation.assigned_ngo_id = payload.destination_ngo_id
    if donation.status == DonationStatus.AVAILABLE:
        donation.status = DonationStatus.RESERVED

    await db.flush()

    return DeliveryCreateResponse(
        id=delivery.id,
        donation_id=delivery.donation_id,
        destination_ngo_id=delivery.destination_ngo_id,
        status=delivery.status,
        pickup_otp=pickup_otp_plain,
        dropoff_otp=dropoff_otp_plain,
        estimated_distance_km=delivery.estimated_distance_km,
        estimated_duration_mins=delivery.estimated_duration_mins,
        created_at=now,
        message=(
            "Delivery task created. Share pickup_otp with donor, "
            "and retain dropoff_otp for NGO dropoff confirmation."
        ),
    )


@router.get(
    "",
    response_model=List[DeliveryResponse],
    summary="List Deliveries",
    description="Drivers, NGOs, and Admins list available or assigned delivery jobs.",
)
async def list_deliveries(
    delivery_status: Optional[DeliveryStatus] = Query(None, alias="status"),
    unassigned_only: bool = Query(False, description="Filter for unassigned driver tasks"),
    limit: int = Query(50, ge=1, le=100),
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[DeliveryResponse]:
    """Lists delivery tasks matching user scope and filters."""
    query = select(Delivery).limit(limit)

    if delivery_status:
        query = query.where(Delivery.status == delivery_status)

    if unassigned_only:
        query = query.where(Delivery.driver_id.is_(None), Delivery.status == DeliveryStatus.ASSIGNED)
    elif current_user.role == UserRole.DRIVER:
        query = query.where(
            (Delivery.driver_id == current_user.id) | (Delivery.driver_id.is_(None))
        )
    elif current_user.role == UserRole.NGO and current_user.ngo_details:
        query = query.where(Delivery.destination_ngo_id == current_user.ngo_details.id)

    result = await db.execute(query)
    deliveries = result.scalars().all()
    return [_format_delivery_response(d) for d in deliveries]


@router.get(
    "/{delivery_id}",
    response_model=DeliveryResponse,
    summary="Get Delivery Details",
)
async def get_delivery(
    delivery_id: uuid.UUID,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeliveryResponse:
    """Fetches details for a single delivery."""
    query = select(Delivery).where(Delivery.id == delivery_id)
    delivery = (await db.execute(query)).scalar_one_or_none()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery '{delivery_id}' was not found.",
        )
    return _format_delivery_response(delivery)


@router.post(
    "/{delivery_id}/accept",
    response_model=AcceptDeliveryResponse,
    status_code=status.HTTP_200_OK,
    summary="Driver Accepts Delivery Task",
    description="Driver claims an assigned delivery task and commits to pickup.",
)
async def accept_delivery_task(
    delivery_id: uuid.UUID,
    current_user: Profile = Depends(require_role(UserRole.DRIVER)),
    db: AsyncSession = Depends(get_db),
) -> AcceptDeliveryResponse:
    """Driver atomically claims an available delivery task."""
    query = (
        select(Delivery)
        .where(Delivery.id == delivery_id)
        .with_for_update()
    )
    delivery = (await db.execute(query)).scalar_one_or_none()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery '{delivery_id}' was not found.",
        )

    if delivery.driver_id is not None and delivery.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This delivery task has already been claimed by another driver.",
        )

    if delivery.status not in (DeliveryStatus.ASSIGNED, DeliveryStatus.ACCEPTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot accept delivery in status '{delivery.status.value}'.",
        )

    delivery.driver_id = current_user.id
    delivery.status = DeliveryStatus.ACCEPTED
    delivery.updated_at = datetime.now(timezone.utc)

    await db.flush()

    return AcceptDeliveryResponse(
        delivery_id=delivery.id,
        driver_id=current_user.id,
        status=delivery.status,
        message="Delivery task accepted. Please navigate to donor pickup location.",
    )


@router.post(
    "/{delivery_id}/pickup-verify",
    response_model=VerifyPickupResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Donor Pickup Handshake",
    description="Driver inputs donor's 6-digit OTP upon arrival to verify physical goods transfer.",
)
async def verify_donor_pickup(
    delivery_id: uuid.UUID,
    payload: VerifyPickupRequest = Body(...),
    current_user: Profile = Depends(require_any_role([UserRole.DRIVER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> VerifyPickupResponse:
    """Validates donor's 6-digit pickup OTP and transitions delivery to PICKED_UP."""
    query = (
        select(Delivery)
        .options(selectinload(Delivery.donation))
        .where(Delivery.id == delivery_id)
        .with_for_update()
    )
    delivery = (await db.execute(query)).scalar_one_or_none()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery '{delivery_id}' was not found.",
        )

    if current_user.role != UserRole.ADMIN and delivery.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the designated driver assigned to this delivery.",
        )

    if delivery.status not in (DeliveryStatus.ACCEPTED, DeliveryStatus.ASSIGNED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot execute pickup handshake when delivery status is '{delivery.status.value}'.",
        )

    if not verify_otp(payload.pickup_otp, delivery.pickup_otp_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pickup code. Please request the donor to confirm their code.",
        )

    now = datetime.now(timezone.utc)
    delivery.status = DeliveryStatus.PICKED_UP
    delivery.picked_up_at = now
    delivery.updated_at = now

    if payload.proof_of_pickup_url:
        delivery.proof_of_pickup_url = payload.proof_of_pickup_url.strip()

    if payload.current_latitude is not None and payload.current_longitude is not None:
        delivery.current_driver_location = create_point_geography(
            longitude=payload.current_longitude,
            latitude=payload.current_latitude,
            srid=settings.POSTGIS_SRID,
        )

    if delivery.donation:
        delivery.donation.status = DonationStatus.IN_TRANSIT
        delivery.donation.updated_at = now

    await db.flush()

    return VerifyPickupResponse(
        delivery_id=delivery.id,
        status=delivery.status,
        picked_up_at=now,
        proof_of_pickup_url=delivery.proof_of_pickup_url,
        message="Pickup verified successfully. Supplies are now in transit to recipient NGO.",
    )


@router.post(
    "/{delivery_id}/dropoff-verify",
    response_model=VerifyDropoffResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify NGO Dropoff Handshake",
    description="Driver inputs NGO's 6-digit OTP and uploads mandatory drop-off photo proof.",
)
async def verify_ngo_dropoff(
    delivery_id: uuid.UUID,
    payload: VerifyDropoffRequest = Body(...),
    current_user: Profile = Depends(require_any_role([UserRole.DRIVER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> VerifyDropoffResponse:
    """Validates destination NGO dropoff OTP and mandatory photo proof to complete delivery."""
    query = (
        select(Delivery)
        .options(selectinload(Delivery.donation))
        .where(Delivery.id == delivery_id)
        .with_for_update()
    )
    delivery = (await db.execute(query)).scalar_one_or_none()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery '{delivery_id}' was not found.",
        )

    if current_user.role != UserRole.ADMIN and delivery.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the designated driver assigned to this delivery.",
        )

    if delivery.status not in (DeliveryStatus.PICKED_UP, DeliveryStatus.IN_TRANSIT):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot execute dropoff handshake when delivery status is '{delivery.status.value}'.",
        )

    if not payload.proof_of_delivery_url or len(payload.proof_of_delivery_url.strip()) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mandatory image proof of delivery URL is required to complete the dropoff handshake.",
        )

    if not verify_otp(payload.dropoff_otp, delivery.delivery_otp_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 6-digit dropoff OTP. Please obtain the confirmation code from recipient NGO staff.",
        )

    now = datetime.now(timezone.utc)
    delivery.status = DeliveryStatus.DELIVERED
    delivery.delivered_at = now
    delivery.proof_of_delivery_url = payload.proof_of_delivery_url.strip()
    delivery.updated_at = now

    if payload.current_latitude is not None and payload.current_longitude is not None:
        delivery.current_driver_location = create_point_geography(
            longitude=payload.current_longitude,
            latitude=payload.current_latitude,
            srid=settings.POSTGIS_SRID,
        )

    if delivery.donation:
        delivery.donation.status = DonationStatus.COMPLETED
        delivery.donation.updated_at = now

    await db.flush()

    return VerifyDropoffResponse(
        delivery_id=delivery.id,
        status=delivery.status,
        delivered_at=now,
        proof_of_delivery_url=delivery.proof_of_delivery_url,
        message="Dropoff handshake confirmed. Donation delivery completed successfully.",
    )


@router.patch(
    "/{delivery_id}/location",
    response_model=DeliveryResponse,
    summary="Update Driver Location Telemetry",
)
async def update_delivery_location(
    delivery_id: uuid.UUID,
    payload: DriverLocationUpdate = Body(...),
    current_user: Profile = Depends(require_any_role([UserRole.DRIVER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> DeliveryResponse:
    """Updates driver's live GPS point during active transit."""
    query = select(Delivery).where(Delivery.id == delivery_id)
    delivery = (await db.execute(query)).scalar_one_or_none()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery '{delivery_id}' was not found.",
        )

    if current_user.role != UserRole.ADMIN and delivery.driver_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    delivery.current_driver_location = create_point_geography(
        longitude=payload.longitude,
        latitude=payload.latitude,
        srid=settings.POSTGIS_SRID,
    )
    if payload.status:
        delivery.status = payload.status

    delivery.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return _format_delivery_response(delivery)
