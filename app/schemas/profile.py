"""Pydantic v2 Schemas for Profiles & Geospatial Coordinates"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class CoordinateSchema(BaseModel):
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")


class ProfileBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=25)
    avatar_url: Optional[str] = None
    address_line: Optional[str] = None


class ProfileCreate(ProfileBase):
    role: UserRole = UserRole.DONOR
    location: Optional[CoordinateSchema] = None


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    address_line: Optional[str] = None
    location: Optional[CoordinateSchema] = None


class ProfileResponse(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
