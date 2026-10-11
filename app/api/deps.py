"""FastAPI Dependency Injection Providers

Supplies database sessions, authentication token extraction, current user resolution,
and dynamic role-guard security factories.
"""

import uuid
from typing import Callable, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.security import TokenPayload, decode_access_token
from app.models.enums import UserRole
from app.models.profile import Profile

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=True,
)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> Profile:
    """Validates JWT access token and resolves active user Profile from database.

    Raises:
        HTTPException 401: If token is expired, invalid, or user does not exist.
        HTTPException 403: If user account has been deactivated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session has expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data: TokenPayload | None = decode_access_token(token)
    if token_data is None or token_data.token_type != "access":
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(token_data.sub)
    except (ValueError, TypeError):
        raise credentials_exception

    query = (
        select(Profile)
        .options(selectinload(Profile.ngo_details))
        .where(Profile.id == user_uuid)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support.",
        )

    return user


def require_role(role: UserRole) -> Callable:
    """Role-guard factory enforcing that the authenticated user possesses a specific role.

    System administrators (`UserRole.ADMIN`) automatically bypass single-role constraints.

    Usage:
        @router.post("/donations")
        async def create_donation(user: Profile = Depends(require_role(UserRole.DONOR))):
            ...
    """
    async def role_checker(
        current_user: Profile = Depends(get_current_user),
    ) -> Profile:
        if current_user.role != role and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Insufficient permissions. Required role: '{role.value}', "
                    f"your role: '{current_user.role.value}'."
                ),
            )
        return current_user

    return role_checker


def require_any_role(roles: List[UserRole]) -> Callable:
    """Role-guard factory enforcing that the authenticated user possesses ANY of the listed roles.

    System administrators (`UserRole.ADMIN`) automatically bypass multi-role constraints.

    Usage:
        @router.get("/deliveries")
        async def list_deliveries(
            user: Profile = Depends(require_any_role([UserRole.DRIVER, UserRole.NGO]))
        ):
            ...
    """
    async def any_role_checker(
        current_user: Profile = Depends(get_current_user),
    ) -> Profile:
        if current_user.role not in roles and current_user.role != UserRole.ADMIN:
            allowed = ", ".join(f"'{r.value}'" for r in roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Insufficient permissions. Allowed roles: [{allowed}], "
                    f"your role: '{current_user.role.value}'."
                ),
            )
        return current_user

    return any_role_checker
