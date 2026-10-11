"""Donations Lifecycle API Endpoints for Save The Serve (S.T.S)

Implements:
1. POST /donations: Create physical, direct monetary, or earmarked donations.
2. GET /donations/feed: Geospatial discovery feed with PostGIS radius filtering and urgency tags.
3. POST /donations/{id}/claim: NGO claims donation with a 15-minute concurrency lock.
4. POST /donations/earmarked-fund: Creates an escrow purchasing transaction intent for supplies.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db, require_any_role, require_role
from app.core.config import settings
from app.core.database import create_point_geography, parse_geography_point
from app.models.donation import Donation
from app.models.enums import DonationKind, DonationStatus, ItemCategory, UserRole
from app.models.ngo import NGODetail
from app.models.profile import Profile
from app.schemas.donation import (
    ClaimDonationResponse,
    DirectMonetaryDonationCreate,
    DonationCreateRequest,
    DonationFeedItem,
    DonationResponse,
    EarmarkedFundRequest,
    EarmarkedMonetaryDonationCreate,
    EscrowIntentResponse,
    PaymentConfirmRequest,
    PaymentConfirmResponse,
    PhysicalDonationCreate,
)
from app.schemas.profile import CoordinateSchema
from app.services.matching_engine import find_nearby_donations

router = APIRouter()


def _format_donation_response(donation: Donation) -> DonationResponse:
    """Helper to transform ORM Donation into validated DonationResponse."""
    coords: Optional[CoordinateSchema] = None
    parsed_pt = parse_geography_point(donation.pickup_location)
    if parsed_pt:
        lon, lat = parsed_pt
        coords = CoordinateSchema(longitude=lon, latitude=lat)

    now_dt = datetime.now(timezone.utc)
    return DonationResponse(
        id=donation.id,
        donor_id=donation.donor_id,
        assigned_ngo_id=donation.assigned_ngo_id,
        kind=donation.kind,
        category=donation.category,
        status=donation.status,
        title=donation.title,
        description=donation.description,
        quantity_amount=donation.quantity_amount,
        quantity_unit=donation.quantity_unit,
        monetary_currency=donation.monetary_currency,
        earmarked_cause=donation.earmarked_cause,
        pickup_address=donation.pickup_address,
        pickup_location=coords,
        pickup_window_start=donation.pickup_window_start,
        pickup_window_end=donation.pickup_window_end,
        is_perishable=donation.is_perishable,
        prepared_at=donation.prepared_at,
        expiry_time=donation.expiry_time,
        reserved_until=donation.reserved_until,
        dietary_tags=donation.dietary_tags or [],
        image_urls=donation.image_urls or [],
        metadata_json=donation.metadata_json or {},
        created_at=donation.created_at or now_dt,
        updated_at=donation.updated_at or now_dt,
    )


@router.post(
    "",
    response_model=DonationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Donation",
    description="Donor creates a physical supply batch, direct monetary contribution, or earmarked funding.",
)
async def create_donation(
    payload: DonationCreateRequest = Body(...),
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DonationResponse:
    """Creates a new donation according to its designated kind."""
    donation_id = uuid.uuid4()

    if isinstance(payload, PhysicalDonationCreate):
        point_geo = create_point_geography(
            longitude=payload.pickup_location.longitude,
            latitude=payload.pickup_location.latitude,
            srid=settings.POSTGIS_SRID,
        )
        metadata = {}
        if payload.custom_category_note:
            metadata["custom_category_note"] = payload.custom_category_note

        donation = Donation(
            id=donation_id,
            donor_id=current_user.id,
            kind=DonationKind.PHYSICAL_ITEM,
            category=payload.category,
            status=DonationStatus.AVAILABLE,
            title=payload.title.strip(),
            description=payload.description.strip() if payload.description else None,
            quantity_amount=payload.quantity_amount,
            quantity_unit=payload.quantity_unit.strip(),
            pickup_address=payload.pickup_address.strip(),
            pickup_location=point_geo,
            pickup_window_start=payload.pickup_window_start,
            pickup_window_end=payload.pickup_window_end,
            is_perishable=payload.is_perishable,
            prepared_at=payload.prepared_at,
            expiry_time=payload.expires_at,
            dietary_tags=payload.dietary_tags or [],
            image_urls=payload.image_urls or [],
            metadata_json=metadata,
        )
        db.add(donation)

    elif isinstance(payload, DirectMonetaryDonationCreate):
        ngo_query = select(NGODetail).where(NGODetail.id == payload.target_ngo_id)
        target_ngo = (await db.execute(ngo_query)).scalar_one_or_none()
        if not target_ngo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target NGO with ID '{payload.target_ngo_id}' does not exist.",
            )

        metadata = {}
        if payload.donor_note:
            metadata["donor_note"] = payload.donor_note
        if payload.payment_method_id:
            metadata["payment_method_id"] = payload.payment_method_id

        donation = Donation(
            id=donation_id,
            donor_id=current_user.id,
            assigned_ngo_id=target_ngo.id,
            kind=DonationKind.MONETARY_DIRECT,
            status=DonationStatus.COMPLETED,
            title=payload.title.strip() if payload.title else "Direct NGO Monetary Contribution",
            description=payload.donor_note,
            quantity_amount=payload.amount,
            quantity_unit="currency",
            monetary_currency=payload.currency.upper(),
            is_perishable=False,
            metadata_json=metadata,
        )
        db.add(donation)

    elif isinstance(payload, EarmarkedMonetaryDonationCreate):
        ngo_query = select(NGODetail).where(NGODetail.id == payload.target_ngo_id)
        target_ngo = (await db.execute(ngo_query)).scalar_one_or_none()
        if not target_ngo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target NGO with ID '{payload.target_ngo_id}' does not exist.",
            )

        metadata = {
            "earmarked_item": payload.item_name,
            "units_count": payload.units_count,
            "cost_per_unit": float(payload.cost_per_unit),
            "total_funded": float(payload.total_amount_funded),
            "donor_note": payload.donor_note,
        }

        donation = Donation(
            id=donation_id,
            donor_id=current_user.id,
            assigned_ngo_id=target_ngo.id,
            kind=DonationKind.MONETARY_EARMARKED,
            status=DonationStatus.AVAILABLE,
            title=f"Earmarked Aid: {payload.item_name.strip()}",
            description=payload.donor_note,
            quantity_amount=payload.total_amount_funded,
            quantity_unit="units",
            monetary_currency=payload.currency.upper(),
            earmarked_cause=payload.item_name.strip(),
            is_perishable=False,
            metadata_json=metadata,
        )
        db.add(donation)

    await db.flush()
    await db.refresh(donation)
    return _format_donation_response(donation)


@router.get(
    "/feed",
    response_model=List[DonationFeedItem],
    status_code=status.HTTP_200_OK,
    summary="Geospatial Donations Feed",
    description="NGOs and drivers discover nearby available food and supplies filtered by radius, category, and urgency.",
)
async def get_donations_feed(
    lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Center latitude override"),
    lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Center longitude override"),
    radius_km: float = Query(25.0, gt=0, le=150.0, description="Search radius in kilometers"),
    category: Optional[ItemCategory] = Query(None, description="Item category filter"),
    kind: Optional[DonationKind] = Query(None, description="Donation kind filter"),
    urgency: Optional[str] = Query(None, pattern="^(critical|high|normal)$", description="Salvage urgency filter"),
    limit: int = Query(50, ge=1, le=100, description="Max feed items"),
    current_user: Profile = Depends(require_any_role([UserRole.NGO, UserRole.DRIVER])),
    db: AsyncSession = Depends(get_db),
) -> List[DonationFeedItem]:
    """Returns geospatial feed of open donations using PostGIS ST_DWithin and ST_Distance."""
    center_lat = lat
    center_lon = lon

    if center_lat is None or center_lon is None:
        if current_user.ngo_details and current_user.ngo_details.hq_location:
            pt = parse_geography_point(current_user.ngo_details.hq_location)
            if pt:
                center_lon, center_lat = pt
        elif current_user.location:
            pt = parse_geography_point(current_user.location)
            if pt:
                center_lon, center_lat = pt

    if center_lat is None or center_lon is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameters 'lat' and 'lon' are required because no default location is configured for your profile.",
        )

    matches = await find_nearby_donations(
        db=db,
        center_latitude=center_lat,
        center_longitude=center_lon,
        radius_km=radius_km,
        category=category,
        kind=kind,
        urgency_filter=urgency,
        limit=limit,
    )

    feed_items: List[DonationFeedItem] = []
    for match in matches:
        base_resp = _format_donation_response(match.donation)
        feed_items.append(
            DonationFeedItem(
                **base_resp.model_dump(),
                distance_km=match.distance_km,
                urgency_level=match.urgency_level,
                is_claimable=match.is_claimable,
            )
        )

    return feed_items


@router.post(
    "/{donation_id}/claim",
    response_model=ClaimDonationResponse,
    status_code=status.HTTP_200_OK,
    summary="Claim Donation with 15-Minute Lock",
    description="NGO claims an available donation, creating an atomic 15-minute concurrency reservation lock.",
)
async def claim_donation(
    donation_id: uuid.UUID,
    current_user: Profile = Depends(require_role(UserRole.NGO)),
    db: AsyncSession = Depends(get_db),
) -> ClaimDonationResponse:
    """Atomically claims a donation for an NGO with a 15-minute reservation lock."""
    if not current_user.ngo_details:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must have an approved NGO organization associated with your profile to claim donations.",
        )

    ngo_id = current_user.ngo_details.id
    now = datetime.now(timezone.utc)
    lock_duration = timedelta(minutes=15)
    new_reserved_until = now + lock_duration

    query = (
        select(Donation)
        .where(Donation.id == donation_id)
        .with_for_update()
    )
    result = await db.execute(query)
    donation = result.scalar_one_or_none()

    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donation with ID '{donation_id}' was not found.",
        )

    if donation.is_perishable and donation.expiry_time:
        exp = donation.expiry_time if donation.expiry_time.tzinfo else donation.expiry_time.replace(tzinfo=timezone.utc)
        if exp <= now:
            donation.status = DonationStatus.EXPIRED
            await db.flush()
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="This perishable donation has expired and can no longer be claimed.",
            )

    if donation.status == DonationStatus.RESERVED:
        if donation.reserved_until and donation.reserved_until > now:
            if donation.assigned_ngo_id != ngo_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Donation is currently locked by another NGO until "
                        f"{donation.reserved_until.strftime('%H:%M:%S UTC')}. "
                        "Try again if their lock expires."
                    ),
                )
    elif donation.status != DonationStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Donation cannot be claimed because its status is '{donation.status.value}'.",
        )

    donation.status = DonationStatus.RESERVED
    donation.assigned_ngo_id = ngo_id
    donation.reserved_until = new_reserved_until

    await db.flush()

    return ClaimDonationResponse(
        donation_id=donation.id,
        assigned_ngo_id=ngo_id,
        status=donation.status,
        reserved_until=new_reserved_until,
        reservation_lock_minutes=15,
        message=(
            "Donation successfully locked for 15 minutes. "
            "Please dispatch a driver or confirm logistics intake before lock expires."
        ),
    )


@router.post(
    "/earmarked-fund",
    response_model=EscrowIntentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Earmarked Escrow Funding Intent",
    description="Creates an escrow funding transaction intent for targeted procurement of supplies (e.g. '50 Blankets').",
)
async def create_earmarked_fund_intent(
    fund_request: EarmarkedFundRequest,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EscrowIntentResponse:
    """Creates an escrow purchasing transaction intent for bulk item aid."""
    ngo_query = select(NGODetail).where(NGODetail.id == fund_request.target_ngo_id)
    target_ngo = (await db.execute(ngo_query)).scalar_one_or_none()
    if not target_ngo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target NGO with ID '{fund_request.target_ngo_id}' was not found.",
        )

    escrow_tx_id = uuid.uuid4()
    donation_id = uuid.uuid4()
    client_secret = f"escrow_pi_{uuid.uuid4().hex[:28]}"

    donation = Donation(
        id=donation_id,
        donor_id=current_user.id,
        assigned_ngo_id=target_ngo.id,
        kind=DonationKind.MONETARY_EARMARKED,
        status=DonationStatus.PENDING,
        title=f"Earmarked Aid: {fund_request.item_name.strip()}",
        description=fund_request.donor_note,
        quantity_amount=fund_request.total_amount_funded,
        quantity_unit="items",
        monetary_currency=fund_request.currency.upper(),
        earmarked_cause=fund_request.item_name.strip(),
        is_perishable=False,
        metadata_json={
            "escrow_transaction_id": str(escrow_tx_id),
            "escrow_status": "intent_created",
            "item_name": fund_request.item_name,
            "earmarked_item_name": fund_request.item_name,
            "units_count": fund_request.units_count,
            "cost_per_unit": float(fund_request.cost_per_unit),
            "client_secret": client_secret,
            "target_ngo_name": target_ngo.organization_name,
        },
    )
    db.add(donation)
    await db.flush()

    return EscrowIntentResponse(
        escrow_transaction_id=escrow_tx_id,
        donation_id=donation_id,
        target_ngo_id=target_ngo.id,
        item_name=fund_request.item_name,
        units_count=fund_request.units_count,
        cost_per_unit=fund_request.cost_per_unit,
        total_amount=fund_request.total_amount_funded,
        currency=fund_request.currency.upper(),
        client_secret=client_secret,
        escrow_status="intent_created",
        message=(
            f"Escrow transaction intent created for '{fund_request.item_name}'. "
            f"Funds will be held in escrow for {target_ngo.organization_name} upon payment confirmation."
        ),
    )


@router.post(
    "/earmarked-fund/{donation_id}/confirm",
    response_model=PaymentConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm Earmarked Escrow Payment",
    description="Confirms payment settlement for an earmarked escrow intent, transitioning status from PENDING to COMPLETED.",
)
async def confirm_earmarked_payment(
    donation_id: uuid.UUID,
    payload: Optional[PaymentConfirmRequest] = Body(default=None),
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentConfirmResponse:
    """Confirms payment settlement for an earmarked escrow intent."""
    query = (
        select(Donation)
        .where(Donation.id == donation_id)
        .with_for_update()
    )
    result = await db.execute(query)
    donation = result.scalar_one_or_none()

    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donation with ID '{donation_id}' was not found.",
        )

    if donation.kind not in (DonationKind.MONETARY_EARMARKED, DonationKind.MONETARY_DIRECT):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment confirmation only applies to monetary donations.",
        )

    if donation.status != DonationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm payment for donation in status '{donation.status.value}'.",
        )

    pay_status = (payload.payment_status if payload else "succeeded").lower().strip()
    payment_tx_id = (payload.payment_intent_id if payload and payload.payment_intent_id else f"pay_{uuid.uuid4().hex[:16]}")
    now = datetime.now(timezone.utc)

    meta = dict(donation.metadata_json or {})

    if pay_status in ("succeeded", "paid", "completed"):
        donation.status = DonationStatus.COMPLETED
        donation.updated_at = now
        meta["escrow_status"] = "funded"
        meta["payment_status"] = "succeeded"
        meta["payment_transaction_id"] = payment_tx_id
        meta["confirmed_at"] = now.isoformat()
        donation.metadata_json = meta
        await db.flush()

        return PaymentConfirmResponse(
            donation_id=donation.id,
            status=donation.status,
            escrow_status="funded",
            total_amount=donation.quantity_amount,
            currency=donation.monetary_currency or "USD",
            target_ngo_id=donation.assigned_ngo_id,
            payment_id=payment_tx_id,
            confirmed_at=now,
            message="Payment settlement successful. Escrow funds allocated to target NGO for procurement.",
        )
    else:
        donation.status = DonationStatus.CANCELLED
        donation.updated_at = now
        meta["escrow_status"] = "payment_failed"
        meta["payment_status"] = pay_status
        donation.metadata_json = meta
        await db.flush()

        return PaymentConfirmResponse(
            donation_id=donation.id,
            status=donation.status,
            escrow_status="payment_failed",
            total_amount=donation.quantity_amount,
            currency=donation.monetary_currency or "USD",
            target_ngo_id=donation.assigned_ngo_id,
            payment_id=payment_tx_id,
            confirmed_at=now,
            message=f"Payment failed with status '{pay_status}'. Donation cancelled.",
        )


@router.post(
    "/payment-webhook",
    status_code=status.HTTP_200_OK,
    summary="Payment Gateway Webhook Listener",
    description="Processes asynchronous payment events (e.g. Stripe payment_intent.succeeded or Razorpay payment.captured).",
)
async def payment_webhook(
    event_data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Processes asynchronous payment events from payment gateways."""
    event_type = event_data.get("type") or event_data.get("event") or event_data.get("payment_status")
    data_object = event_data.get("data", {}).get("object", {}) or event_data.get("payload", {}).get("payment", {}).get("entity", {})

    metadata = data_object.get("metadata", {})
    donation_id_str = (
        metadata.get("donation_id")
        or data_object.get("notes", {}).get("donation_id")
        or event_data.get("donation_id")
        or data_object.get("donation_id")
    )

    if not donation_id_str:
        return {"received": True, "action": "ignored_no_donation_id"}

    try:
        donation_uuid = uuid.UUID(str(donation_id_str))
    except ValueError:
        return {"received": True, "action": "invalid_donation_id_format"}

    query = (
        select(Donation)
        .where(Donation.id == donation_uuid)
        .with_for_update()
    )
    donation = (await db.execute(query)).scalar_one_or_none()
    if not donation:
        return {"received": True, "action": "donation_not_found"}

    gateway_ref = (
        event_data.get("payment_gateway_ref")
        or event_data.get("id")
        or data_object.get("id")
        or f"pay_{uuid.uuid4().hex[:12]}"
    )
    normalized_status = str(
        event_data.get("payment_status")
        or event_type
        or data_object.get("status")
        or ""
    ).lower().strip()

    now = datetime.now(timezone.utc)
    if normalized_status in (
        "completed",
        "succeeded",
        "payment_intent.succeeded",
        "payment.captured",
        "charge.succeeded",
        "paid",
    ):
        donation.status = DonationStatus.COMPLETED
        meta = dict(donation.metadata_json or {})
        meta["escrow_status"] = "funded"
        meta["payment_status"] = "completed"
        meta["payment_gateway_ref"] = gateway_ref
        meta["ledger_status"] = "credited"
        meta["gateway_event_id"] = gateway_ref
        meta["confirmed_at"] = now.isoformat()
        donation.metadata_json = meta
        donation.updated_at = now
        await db.flush()
        return {
            "received": True,
            "action": "donation_completed",
            "donation_id": str(donation.id),
            "status": donation.status.value,
            "payment_status": "completed",
            "payment_gateway_ref": gateway_ref,
            "ledger_status": "credited",
        }
    elif normalized_status in (
        "failed",
        "payment_intent.payment_failed",
        "payment.failed",
        "cancelled",
    ):
        donation.status = DonationStatus.CANCELLED
        meta = dict(donation.metadata_json or {})
        meta["escrow_status"] = "failed"
        meta["payment_status"] = "failed"
        meta["payment_gateway_ref"] = gateway_ref
        donation.metadata_json = meta
        donation.updated_at = now
        await db.flush()
        return {
            "received": True,
            "action": "donation_cancelled",
            "donation_id": str(donation.id),
            "status": donation.status.value,
        }

    return {"received": True, "action": "unhandled_event_type"}


@router.post(
    "/{donation_id}/complete",
    response_model=DonationResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark Donation Intake Completed",
    description="NGO or Admin finalizes donation intake status after physical or monetary receipt.",
)
async def complete_donation(
    donation_id: uuid.UUID,
    current_user: Profile = Depends(require_any_role([UserRole.NGO, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> DonationResponse:
    """Finalizes donation intake lifecycle, marking status as COMPLETED."""
    query = (
        select(Donation)
        .where(Donation.id == donation_id)
        .with_for_update()
    )
    donation = (await db.execute(query)).scalar_one_or_none()
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donation with ID '{donation_id}' was not found.",
        )

    now = datetime.now(timezone.utc)
    donation.status = DonationStatus.COMPLETED
    donation.updated_at = now
    await db.flush()

    return _format_donation_response(donation)
