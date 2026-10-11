"""Public NGO Directory & Capacity Management Endpoints for Save The Serve (S.T.S)

Implements:
1. GET /ngos: Public directory lookup with PostGIS location search, distance calculation,
   contact info, capacity status toggles, and accepted donation categories.
2. GET /ngos/{id}: Detailed public profile of an individual NGO.
3. PATCH /ngos/{id}/capacity: NGO coordinator updates capacity intake toggle & accepted categories.
4. POST /ngos/register: Initial registration of NGO details for profile.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from geoalchemy2 import Geography
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db, require_any_role, require_role
from app.core.config import settings
from app.core.database import create_point_geography, parse_geography_point
from app.models.enums import ItemCategory, UserRole
from app.models.ngo import NGODetail
from app.models.profile import Profile
from app.schemas.ngo import (
    NGOCapacityUpdateRequest,
    NGODetailCreate,
    NGODirectoryItem,
    encode_ngo_capacity_meta,
    parse_ngo_capacity_meta,
)
from app.schemas.profile import CoordinateSchema

router = APIRouter()


def _format_ngo_directory_item(
    ngo: NGODetail, distance_meters: Optional[float] = None
) -> NGODirectoryItem:
    """Transforms ORM NGODetail into enriched NGODirectoryItem with capacity metadata."""
    coords: Optional[CoordinateSchema] = None
    if ngo.hq_location is not None:
        pt = parse_geography_point(ngo.hq_location)
        if pt:
            coords = CoordinateSchema(longitude=pt[0], latitude=pt[1])

    dist_km = round(distance_meters / 1000.0, 2) if distance_meters is not None else None

    desc_text, is_accepting, accepted_cats = parse_ngo_capacity_meta(ngo.capacity_description)

    now_dt = datetime.now(timezone.utc)
    return NGODirectoryItem(
        id=ngo.id,
        organization_name=ngo.organization_name,
        registration_number=ngo.registration_number,
        tax_exemption_number=ngo.tax_exemption_number,
        operating_radius_km=ngo.operating_radius_km,
        hq_location=coords,
        distance_km=dist_km,
        is_approved=ngo.is_approved,
        website_url=ngo.website_url,
        contact_email=ngo.contact_email,
        contact_phone=ngo.contact_phone,
        emergency_phone_number=ngo.contact_phone,
        operational_hours="08:00 - 20:00 Daily",
        capacity_description=desc_text,
        is_accepting_donations=is_accepting,
        capacity_status="accepting" if is_accepting else "at_capacity",
        accepted_categories=accepted_cats,
        created_at=ngo.created_at or now_dt,
        updated_at=ngo.updated_at or now_dt,
    )


@router.get(
    "",
    response_model=List[NGODirectoryItem],
    status_code=status.HTTP_200_OK,
    summary="Public NGO Directory Lookup",
    description="Discover verified NGOs with PostGIS radius search, contact details, capacity toggles, and accepted item categories.",
)
async def list_ngos(
    lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Center latitude for proximity search"),
    lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Center longitude for proximity search"),
    radius_km: Optional[float] = Query(None, gt=0, le=150.0, description="Search radius in kilometers"),
    query: Optional[str] = Query(None, description="Search by organization name or registration number"),
    search: Optional[str] = Query(None, description="Search alias for organization name or registration number"),
    category: Optional[ItemCategory] = Query(None, description="Filter NGOs that accept this donation category"),
    accepting_only: bool = Query(False, description="Filter for NGOs currently accepting donations"),
    approved_only: bool = Query(True, description="Only show approved NGOs (default True)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[NGODirectoryItem]:
    """Public directory lookup with optional geospatial proximity ordering."""
    distance_expr = None
    if lat is not None and lon is not None:
        center_geog = cast(
            func.ST_SetSRID(func.ST_MakePoint(lon, lat), settings.POSTGIS_SRID),
            Geography,
        )
        distance_expr = func.ST_Distance(NGODetail.hq_location, center_geog).label("distance_meters")
        db_query = select(NGODetail, distance_expr)

        if radius_km is not None:
            radius_meters = float(radius_km) * 1000.0
            db_query = db_query.where(
                func.ST_DWithin(NGODetail.hq_location, center_geog, radius_meters)
            )

        db_query = db_query.order_by(distance_expr.asc())
    else:
        db_query = select(NGODetail).order_by(NGODetail.organization_name.asc())

    if approved_only:
        db_query = db_query.where(NGODetail.is_approved.is_(True))

    search_term = query or search
    if search_term:
        search_pattern = f"%{search_term.strip()}%"
        db_query = db_query.where(
            or_(
                NGODetail.organization_name.ilike(search_pattern),
                NGODetail.registration_number.ilike(search_pattern),
            )
        )

    db_query = db_query.offset(offset).limit(limit)
    res = await db.execute(db_query)

    items: List[NGODirectoryItem] = []
    if distance_expr is not None:
        rows = res.all()
        for ngo, dist in rows:
            entry = _format_ngo_directory_item(ngo, distance_meters=dist)
            if accepting_only and not entry.is_accepting_donations:
                continue
            if category is not None and category not in entry.accepted_categories:
                continue
            items.append(entry)
    else:
        ngos = res.scalars().all()
        for ngo in ngos:
            entry = _format_ngo_directory_item(ngo, distance_meters=None)
            if accepting_only and not entry.is_accepting_donations:
                continue
            if category is not None and category not in entry.accepted_categories:
                continue
            items.append(entry)

    return items


@router.get(
    "/{ngo_id}",
    response_model=NGODirectoryItem,
    status_code=status.HTTP_200_OK,
    summary="Get NGO Details",
)
async def get_ngo(
    ngo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> NGODirectoryItem:
    """Retrieves full public directory details of a specific NGO."""
    query = select(NGODetail).where(NGODetail.id == ngo_id)
    ngo = (await db.execute(query)).scalar_one_or_none()
    if not ngo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NGO with ID '{ngo_id}' was not found.",
        )
    return _format_ngo_directory_item(ngo)


@router.patch(
    "/{ngo_id}/capacity",
    response_model=NGODirectoryItem,
    status_code=status.HTTP_200_OK,
    summary="Update NGO Capacity & Accepted Categories",
    description="NGO coordinator toggles donation intake capacity, updates accepted categories, and modifies operating radius.",
)
async def update_ngo_capacity(
    ngo_id: uuid.UUID,
    payload: NGOCapacityUpdateRequest = Body(...),
    current_user: Profile = Depends(require_any_role([UserRole.NGO, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> NGODirectoryItem:
    """Updates NGO intake capacity status and accepted categories."""
    query = select(NGODetail).where(NGODetail.id == ngo_id)
    ngo = (await db.execute(query)).scalar_one_or_none()
    if not ngo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NGO with ID '{ngo_id}' was not found.",
        )

    if current_user.role != UserRole.ADMIN and ngo.profile_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this organization's capacity settings.",
        )

    curr_desc, curr_accepting, curr_cats = parse_ngo_capacity_meta(ngo.capacity_description)

    new_desc = payload.capacity_description if payload.capacity_description is not None else curr_desc
    new_accepting = curr_accepting
    if payload.is_accepting_donations is not None:
        new_accepting = payload.is_accepting_donations
    elif payload.capacity_status is not None:
        from app.schemas.ngo import CapacityStatus
        new_accepting = (payload.capacity_status == CapacityStatus.ACCEPTING)

    new_cats = payload.accepted_categories if payload.accepted_categories is not None else curr_cats

    ngo.capacity_description = encode_ngo_capacity_meta(
        description=new_desc,
        is_accepting=new_accepting,
        accepted_categories=new_cats,
    )

    if payload.operating_radius_km is not None:
        ngo.operating_radius_km = payload.operating_radius_km

    ngo.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return _format_ngo_directory_item(ngo)


@router.post(
    "/register",
    response_model=NGODirectoryItem,
    status_code=status.HTTP_201_CREATED,
    summary="Register NGO Organization",
    description="NGO user registers their organization details, headquarters location, and capacity preferences.",
)
async def register_ngo_organization(
    payload: NGODetailCreate,
    current_user: Profile = Depends(require_any_role([UserRole.NGO, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> NGODirectoryItem:
    """Registers organization directory entry for an authenticated NGO user."""
    existing_query = select(NGODetail).where(NGODetail.profile_id == current_user.id)
    existing = (await db.execute(existing_query)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An NGO organization has already been registered for this account.",
        )

    reg_query = select(NGODetail).where(
        NGODetail.registration_number == payload.registration_number.strip()
    )
    duplicate_reg = (await db.execute(reg_query)).scalar_one_or_none()
    if duplicate_reg:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Registration number '{payload.registration_number}' is already registered.",
        )

    hq_geo = create_point_geography(
        longitude=payload.hq_location.longitude,
        latitude=payload.hq_location.latitude,
        srid=settings.POSTGIS_SRID,
    )

    capacity_str = encode_ngo_capacity_meta(
        description=payload.capacity_description,
        is_accepting=payload.is_accepting_donations,
        accepted_categories=payload.accepted_categories or list(ItemCategory),
    )

    now = datetime.now(timezone.utc)
    ngo_id = uuid.uuid4()
    ngo = NGODetail(
        id=ngo_id,
        profile_id=current_user.id,
        organization_name=payload.organization_name.strip(),
        registration_number=payload.registration_number.strip(),
        tax_exemption_number=payload.tax_exemption_number.strip() if payload.tax_exemption_number else None,
        operating_radius_km=payload.operating_radius_km,
        hq_location=hq_geo,
        is_approved=True,
        website_url=payload.website_url.strip() if payload.website_url else None,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone.strip(),
        capacity_description=capacity_str,
        verification_documents=payload.verification_documents or [],
        created_at=now,
        updated_at=now,
    )
    db.add(ngo)
    await db.flush()

    return _format_ngo_directory_item(ngo)
