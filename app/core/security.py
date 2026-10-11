"""Security & Cryptography Module

Handles password hashing via Passlib/Bcrypt, JWT creation, and token verification helpers.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from uuid import UUID
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    """Structured representation of decoded JWT claims."""
    sub: str
    role: str
    email: Optional[str] = None
    exp: int
    token_type: str = "access"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a secure bcrypt hash from a plaintext password."""
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, UUID],
    role: str,
    email: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a cryptographically signed JWT access token.

    Args:
        subject: Unique identifier of the user (UUID or string).
        role: Primary assigned role of the user (e.g., 'donor', 'ngo', 'driver', 'admin').
        email: Optional email address embedded in claims.
        expires_delta: Optional custom duration override.

    Returns:
        Encoded JWT string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    claims: Dict[str, Any] = {
        "sub": str(subject),
        "role": str(role),
        "email": email,
        "token_type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    encoded_jwt = jwt.encode(
        claims,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, UUID],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a long-lived signed JWT refresh token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    claims: Dict[str, Any] = {
        "sub": str(subject),
        "token_type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        claims,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate a JWT access token against the configured secret key.

    Returns:
        Parsed TokenPayload instance or None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        sub = payload.get("sub")
        role = payload.get("role")
        exp = payload.get("exp")
        token_type = payload.get("token_type", "access")

        if sub is None or role is None or exp is None:
            return None

        return TokenPayload(
            sub=sub,
            role=role,
            email=payload.get("email"),
            exp=exp,
            token_type=token_type,
        )
    except JWTError:
        return None
