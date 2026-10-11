"""Pydantic v2 Schemas for Authentication & Role-Based Profiles"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.enums import UserRole
from app.schemas.profile import CoordinateSchema


class SignUpRequest(BaseModel):
    """Unified user registration payload supporting initial role selection."""
    role: UserRole = Field(
        ...,
        description="Initial role: donor, ngo, or driver (admin registration disallowed via public endpoint)",
    )
    full_name: str = Field(..., min_length=2, max_length=150, description="Full name or company name")
    email: EmailStr = Field(..., description="Unique email address")
    password: str = Field(..., min_length=8, max_length=128, description="Plaintext password (min 8 chars)")
    phone_number: Optional[str] = Field(None, max_length=25, description="Contact phone number")
    address_line: Optional[str] = Field(None, description="Physical address or base office")
    location: Optional[CoordinateSchema] = Field(None, description="Base geographic coordinates")

    organization_name: Optional[str] = Field(None, max_length=255, description="Registered NGO entity name")
    registration_number: Optional[str] = Field(None, max_length=100, description="Government registration code")
    tax_exemption_number: Optional[str] = Field(None, max_length=100, description="Tax exemption identifier")
    operating_radius_km: Optional[Decimal] = Field(default=Decimal("25.0"), gt=0)
    capacity_description: Optional[str] = Field(None, description="Storage, pantry, or distribution capacity")

    @model_validator(mode="after")
    def validate_role_specific_fields(self) -> "SignUpRequest":
        if self.role == UserRole.ADMIN:
            raise ValueError("Admin accounts cannot be self-registered via public signup.")

        if self.role == UserRole.NGO:
            if not self.organization_name:
                raise ValueError("organization_name is required when registering with role 'ngo'.")
            if not self.registration_number:
                raise ValueError("registration_number is required when registering with role 'ngo'.")
            if not self.location:
                raise ValueError("Headquarters geographic coordinates (location) are required for NGOs.")
        return self


class LoginRequest(BaseModel):
    """Unified login payload."""
    email: EmailStr = Field(..., description="Registered account email")
    password: str = Field(..., description="Account password")


class NGOSummary(BaseModel):
    """Brief organization profile for authenticated NGO users."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_name: str
    registration_number: str
    operating_radius_km: Decimal
    is_approved: bool


class UserProfileSummary(BaseModel):
    """Authenticated user profile and role representation."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: UserRole
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    address_line: Optional[str] = None
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    ngo_details: Optional[NGOSummary] = None


class TokenResponse(BaseModel):
    """JWT Token issuance response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfileSummary
