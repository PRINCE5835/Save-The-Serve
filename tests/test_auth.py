"""Unit & Integration Tests for Security, JWT Tokens, and Auth Schemas"""

import pytest
from uuid import uuid4
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.models.enums import UserRole
from app.schemas.auth import SignUpRequest, LoginRequest
from app.core.database import create_point_geography, parse_geography_point


def test_password_hashing():
    """Verify bcrypt password hashing and verification behavior."""
    raw_password = "SecurePassword123!"
    hashed = get_password_hash(raw_password)
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_generation_and_decoding():
    """Verify access token creation, claims encoding, and structured payload recovery."""
    user_id = uuid4()
    role = UserRole.DONOR.value
    email = "donor@example.com"

    token = create_access_token(subject=user_id, role=role, email=email)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.sub == str(user_id)
    assert payload.role == role
    assert payload.email == email
    assert payload.token_type == "access"


def test_invalid_jwt_token():
    """Verify that malformed or forged tokens return None."""
    assert decode_access_token("not.a.valid.jwt.token") is None


def test_ngo_signup_validation():
    """Verify that NGO sign up requires organization_name and registration_number."""
    donor_req = SignUpRequest(
        role=UserRole.DONOR,
        full_name="Jane Donor",
        email="jane@donor.org",
        password="ValidPassword123!",
    )
    assert donor_req.role == UserRole.DONOR

    with pytest.raises(ValueError, match="organization_name is required"):
        SignUpRequest(
            role=UserRole.NGO,
            full_name="NGO Director",
            email="ngo@aid.org",
            password="ValidPassword123!",
            registration_number="REG-12345",
        )

    with pytest.raises(ValueError, match="Admin accounts cannot be self-registered"):
        SignUpRequest(
            role=UserRole.ADMIN,
            full_name="Evil Admin",
            email="hacker@evil.org",
            password="ValidPassword123!",
        )


def test_postgis_spatial_helper():
    """Verify WKTElement creation for WGS84 coordinates."""
    lon, lat = -122.4194, 37.7749
    wkt = create_point_geography(longitude=lon, latitude=lat, srid=4326)
    assert "SRID=4326;POINT(-122.4194 37.7749)" in str(wkt)
