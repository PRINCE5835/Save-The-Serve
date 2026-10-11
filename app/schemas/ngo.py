"""Pydantic v2 Schemas for NGO Details, Public Directory & Capacity Management"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Dict, List, Optional, Tuple
from uuid import UUID
from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field

from app.core.database import parse_geography_point
from app.models.enums import ItemCategory
from app.schemas.profile import CoordinateSchema


def convert_geography_to_coordinate(v: object) -> Optional[CoordinateSchema]:
    if v is None:
        return None
    if isinstance(v, CoordinateSchema):
        return v
    if isinstance(v, dict):
        return CoordinateSchema(**v)
    pt = parse_geography_point(v)
    if pt:
        return CoordinateSchema(longitude=pt[0], latitude=pt[1])
    return None


CoordinateField = Annotated[Optional[CoordinateSchema], BeforeValidator(convert_geography_to_coordinate)]


def parse_ngo_capacity_meta(capacity_desc: Optional[str]) -> Tuple[Optional[str], bool, List[ItemCategory]]:
    """Extracts (description_text, is_accepting_donations, accepted_categories)."""
    if not capacity_desc:
        return (None, True, list(ItemCategory))

    try:
        data = json.loads(capacity_desc)
        if isinstance(data, dict):
            text = data.get("description")
            is_acc = data.get("is_accepting_donations", True)
            raw_cats = data.get("accepted_categories", [])
            valid_cats = []
            for c in raw_cats:
                try:
                    valid_cats.append(ItemCategory(c))
                except ValueError:
                    pass
            return (text, is_acc, valid_cats or list(ItemCategory))
    except Exception:
        pass

    return (capacity_desc, True, list(ItemCategory))


def encode_ngo_capacity_meta(
    description: Optional[str],
    is_accepting: bool,
    accepted_categories: List[ItemCategory],
) -> str:
    """Encodes capacity metadata into structured JSON string for storage in capacity_description column."""
    payload = {
        "description": description,
        "is_accepting_donations": is_accepting,
        "accepted_categories": [c.value for c in accepted_categories],
    }
    return json.dumps(payload)


class NGODetailBase(BaseModel):
    organization_name: str = Field(..., min_length=2, max_length=255)
    registration_number: str = Field(..., max_length=100)
    tax_exemption_number: Optional[str] = Field(None, max_length=100)
    operating_radius_km: Decimal = Field(default=Decimal("25.0"), gt=0)
    contact_email: EmailStr
    contact_phone: str = Field(..., max_length=25)
    website_url: Optional[str] = None
    capacity_description: Optional[str] = None


class NGODetailCreate(NGODetailBase):
    hq_location: CoordinateSchema
    verification_documents: Optional[List[str]] = Field(default_factory=list)
    accepted_categories: Optional[List[ItemCategory]] = Field(
        default_factory=lambda: list(ItemCategory),
        description="Categories accepted for donation intake",
    )
    is_accepting_donations: bool = Field(
        default=True, description="Capacity intake toggle"
    )


class NGODetailResponse(NGODetailBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    hq_location: CoordinateField = None
    is_approved: bool
    created_at: datetime
    updated_at: datetime


from enum import Enum


class CapacityStatus(str, Enum):
    """Emergency capacity intake enum."""
    ACCEPTING = "accepting"
    AT_CAPACITY = "at_capacity"


class NGODirectoryItem(BaseModel):
    """Enriched public directory entry for an approved Non-Profit Organization."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_name: str
    registration_number: str
    tax_exemption_number: Optional[str] = None
    operating_radius_km: Decimal
    hq_location: CoordinateField = None
    distance_km: Optional[float] = Field(
        None, description="Geodesic distance in km from query location"
    )
    is_approved: bool
    website_url: Optional[str] = None
    contact_email: EmailStr
    contact_phone: str
    emergency_phone_number: Optional[str] = Field(
        None, description="Direct 24/7 emergency intake contact number"
    )
    operational_hours: str = Field(
        default="08:00 - 20:00 Daily", description="Public intake operational hours"
    )
    capacity_description: Optional[str] = None
    is_accepting_donations: bool = True
    capacity_status: str = Field(
        default="accepting", description="Capacity status: 'accepting' or 'at_capacity'"
    )
    accepted_categories: List[ItemCategory] = Field(
        default_factory=lambda: list(ItemCategory)
    )
    created_at: datetime
    updated_at: datetime


class NGOCapacityUpdateRequest(BaseModel):
    """Payload for NGO coordinators to toggle intake capacity and accepted items."""
    is_accepting_donations: Optional[bool] = Field(
        None, description="Toggle donation intake capacity active/paused"
    )
    capacity_status: Optional[CapacityStatus] = Field(
        None, description="Emergency capacity status: 'accepting' or 'at_capacity'"
    )
    capacity_description: Optional[str] = Field(
        None, description="Detailed capacity statement (e.g. 'Can receive up to 500 meals daily')"
    )
    accepted_categories: Optional[List[ItemCategory]] = Field(
        None, description="Updated accepted item categories"
    )
    operating_radius_km: Optional[Decimal] = Field(
        None, gt=0, le=150, description="Operating catchment radius in kilometers"
    )
