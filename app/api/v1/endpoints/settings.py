"""User Profile Settings, Password Management & Push Notification Preferences

Implements:
1. GET /settings/profile: View authenticated profile details.
2. PATCH /settings/profile: Update name, phone, avatar, address, and GPS coordinates.
3. POST /settings/password: Securely verify existing password and set new password.
4. GET /settings/notifications: Fetch push notification preferences and device tokens.
5. PUT /settings/notifications: Update push notification toggles and device tokens.
"""

from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.database import create_point_geography, parse_geography_point
from app.core.security import get_password_hash, verify_password
from app.models.profile import Profile
from app.schemas.profile import CoordinateSchema, ProfileResponse, ProfileUpdate
from app.schemas.support import (
    NotificationPreferences,
    NotificationPreferencesResponse,
    PasswordChangeRequest,
    PasswordChangeResponse,
)

router = APIRouter()

_notification_store: Dict[UUID, NotificationPreferences] = {}


def _format_profile_response(user: Profile) -> ProfileResponse:
    return ProfileResponse(
        id=user.id,
        role=user.role,
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        avatar_url=user.avatar_url,
        address_line=user.address_line,
        is_verified=user.is_verified,
        is_active=user.is_active,
        created_at=user.created_at or datetime.now(timezone.utc),
        updated_at=user.updated_at or datetime.now(timezone.utc),
    )


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Get User Profile",
)
async def get_user_profile(
    current_user: Profile = Depends(get_current_user),
) -> ProfileResponse:
    """Returns the authenticated user's profile metadata."""
    return _format_profile_response(current_user)


@router.patch(
    "/profile",
    response_model=ProfileResponse,
    summary="Update User Profile",
)
async def update_user_profile(
    payload: ProfileUpdate = Body(...),
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Updates user contact details, avatar, and default address/GPS location."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()
    if payload.phone_number is not None:
        current_user.phone_number = payload.phone_number.strip()
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url.strip()
    if payload.address_line is not None:
        current_user.address_line = payload.address_line.strip()
    if payload.location is not None:
        current_user.location = create_point_geography(
            longitude=payload.location.longitude,
            latitude=payload.location.latitude,
            srid=settings.POSTGIS_SRID,
        )

    current_user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return _format_profile_response(current_user)


@router.post(
    "/password",
    response_model=PasswordChangeResponse,
    status_code=status.HTTP_200_OK,
    summary="Change User Password",
    description="Verifies the current password before updating to the new password hash.",
)
async def change_password(
    payload: PasswordChangeRequest = Body(...),
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PasswordChangeResponse:
    """Validates existing credentials and updates account password."""
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account does not have an existing password set (OAuth/SSO account).",
        )

    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password verification failed.",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password.",
        )

    now = datetime.now(timezone.utc)
    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.updated_at = now
    await db.flush()

    return PasswordChangeResponse(
        message="Password updated successfully. Please use your new password on subsequent logins.",
        updated_at=now,
    )


@router.get(
    "/notifications",
    response_model=NotificationPreferencesResponse,
    summary="Get Push Notification Preferences",
)
async def get_notification_preferences(
    current_user: Profile = Depends(get_current_user),
) -> NotificationPreferencesResponse:
    """Retrieves current user notification channel settings and device push token."""
    pref = _notification_store.get(
        current_user.id,
        NotificationPreferences(
            push_enabled=True,
            email_enabled=True,
            sms_alerts_enabled=False,
            urgent_surplus_alerts=True,
            fcm_device_token=None,
        ),
    )
    return NotificationPreferencesResponse(
        **pref.model_dump(),
        user_id=current_user.id,
        updated_at=current_user.updated_at or datetime.now(timezone.utc),
    )


@router.put(
    "/notifications",
    response_model=NotificationPreferencesResponse,
    summary="Update Push Notification Preferences",
)
@router.patch(
    "/notifications",
    response_model=NotificationPreferencesResponse,
    summary="Update Push Notification Preferences (Partial)",
)
async def update_notification_preferences(
    payload: NotificationPreferences = Body(...),
    current_user: Profile = Depends(get_current_user),
) -> NotificationPreferencesResponse:
    """Updates push notification toggles and registers Firebase Cloud Messaging (FCM) tokens."""
    _notification_store[current_user.id] = payload
    now = datetime.now(timezone.utc)
    return NotificationPreferencesResponse(
        **payload.model_dump(),
        user_id=current_user.id,
        updated_at=now,
    )
