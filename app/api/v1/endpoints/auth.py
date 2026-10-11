"""Authentication & Identity Router for Save The Serve (S.T.S)

Implements unified registration, authentication, token refresh, and identity inspection.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.database import create_point_geography
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.enums import UserRole
from app.models.ngo import NGODetail
from app.models.profile import Profile
from app.schemas.auth import (
    LoginRequest,
    NGOSummary,
    SignUpRequest,
    TokenResponse,
    UserProfileSummary,
)

router = APIRouter()


def _build_user_summary(profile: Profile) -> UserProfileSummary:
    """Helper to convert Profile ORM object to UserProfileSummary schema."""
    ngo_summary: Optional[NGOSummary] = None
    if profile.ngo_details:
        ngo_summary = NGOSummary(
            id=profile.ngo_details.id,
            organization_name=profile.ngo_details.organization_name,
            registration_number=profile.ngo_details.registration_number,
            operating_radius_km=profile.ngo_details.operating_radius_km,
            is_approved=profile.ngo_details.is_approved,
        )

    now_dt = datetime.now(timezone.utc)
    return UserProfileSummary(
        id=profile.id,
        role=profile.role,
        full_name=profile.full_name,
        email=profile.email,
        phone_number=profile.phone_number,
        avatar_url=profile.avatar_url,
        address_line=profile.address_line,
        is_verified=profile.is_verified,
        is_active=profile.is_active,
        created_at=profile.created_at or now_dt,
        updated_at=profile.updated_at or now_dt,
        ngo_details=ngo_summary,
    )


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Unified User Registration",
    description="Registers a new donor, NGO, or volunteer driver. Disallows self-registration for admin.",
)
async def signup(
    signup_data: SignUpRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Unified Sign Up supporting initial role selection ('donor', 'ngo', 'driver')."""
    normalized_email = signup_data.email.lower().strip()

    existing_user_query = select(Profile).where(Profile.email == normalized_email)
    existing_user = (await db.execute(existing_user_query)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    if signup_data.role == UserRole.NGO and signup_data.registration_number:
        reg_num = signup_data.registration_number.strip()
        existing_ngo_query = select(NGODetail).where(NGODetail.registration_number == reg_num)
        existing_ngo = (await db.execute(existing_ngo_query)).scalar_one_or_none()
        if existing_ngo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An NGO with registration number '{reg_num}' is already registered.",
            )

    hashed_pwd = get_password_hash(signup_data.password)
    point_geo = None
    if signup_data.location:
        point_geo = create_point_geography(
            longitude=signup_data.location.longitude,
            latitude=signup_data.location.latitude,
            srid=settings.POSTGIS_SRID,
        )

    new_user_id = uuid.uuid4()
    now_dt = datetime.now(timezone.utc)
    profile = Profile(
        id=new_user_id,
        role=signup_data.role,
        full_name=signup_data.full_name.strip(),
        email=normalized_email,
        hashed_password=hashed_pwd,
        phone_number=signup_data.phone_number.strip() if signup_data.phone_number else None,
        address_line=signup_data.address_line.strip() if signup_data.address_line else None,
        location=point_geo,
        is_verified=False,
        is_active=True,
        created_at=now_dt,
        updated_at=now_dt,
    )
    db.add(profile)

    if signup_data.role == UserRole.NGO:
        ngo_detail = NGODetail(
            id=uuid.uuid4(),
            profile_id=new_user_id,
            organization_name=signup_data.organization_name.strip(),
            registration_number=signup_data.registration_number.strip(),
            tax_exemption_number=signup_data.tax_exemption_number.strip()
            if signup_data.tax_exemption_number
            else None,
            operating_radius_km=signup_data.operating_radius_km or Decimal("25.0"),
            hq_location=point_geo,
            is_approved=False,
            contact_email=normalized_email,
            contact_phone=signup_data.phone_number.strip() if signup_data.phone_number else "",
            capacity_description=signup_data.capacity_description,
        )
        db.add(ngo_detail)
        profile.ngo_details = ngo_detail

    await db.flush()

    access_token = create_access_token(
        subject=profile.id,
        role=profile.role.value,
        email=profile.email,
    )
    refresh_token = create_refresh_token(subject=profile.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_build_user_summary(profile),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Unified User Login",
    description="Authenticates with email and password, returning JWT tokens and user role profile.",
)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Unified JSON Login endpoint returning JWT tokens and role profile."""
    normalized_email = login_data.email.lower().strip()

    query = (
        select(Profile)
        .options(selectinload(Profile.ngo_details))
        .where(Profile.email == normalized_email)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is deactivated. Please contact support.",
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        email=user.email,
    )
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_build_user_summary(user),
    )


@router.get(
    "/me",
    response_model=UserProfileSummary,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Returns the active authenticated user profile, assigned role, and associated organization details.",
)
async def get_me(
    current_user: Profile = Depends(get_current_user),
) -> UserProfileSummary:
    """Returns the authenticated user's profile and active role."""
    return _build_user_summary(current_user)
