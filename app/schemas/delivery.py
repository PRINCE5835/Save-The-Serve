"""Pydantic v2 Schemas for Deliveries, Driver Handshakes & Live Tracking"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.core.database import parse_geography_point
from app.models.enums import DeliveryStatus
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


class DeliveryBase(BaseModel):
    donation_id: UUID
    destination_ngo_id: UUID
    driver_id: Optional[UUID] = None
    status: DeliveryStatus = DeliveryStatus.ASSIGNED


class DeliveryCreate(BaseModel):
    """Payload to initiate a delivery assignment for a donation."""
    donation_id: UUID = Field(..., description="Donation UUID being transported")
    destination_ngo_id: UUID = Field(..., description="Recipient NGO organization UUID")
    pickup_location: CoordinateSchema = Field(..., description="Donor pickup GPS coordinates")
    dropoff_location: CoordinateSchema = Field(..., description="Destination NGO GPS coordinates")
    estimated_distance_km: Optional[Decimal] = Field(None, ge=0)
    estimated_duration_mins: Optional[int] = Field(None, ge=0)


class DeliveryCreateResponse(BaseModel):
    """Result of delivery creation containing generated OTPs for authorized parties."""
    id: UUID
    donation_id: UUID
    destination_ngo_id: UUID
    status: DeliveryStatus
    pickup_otp: str = Field(..., description="6-digit OTP for donor pickup handshake")
    dropoff_otp: str = Field(..., description="6-digit OTP for NGO dropoff handshake")
    estimated_distance_km: Optional[Decimal] = None
    estimated_duration_mins: Optional[int] = None
    created_at: datetime
    message: str


class AcceptDeliveryResponse(BaseModel):
    """Result of driver claiming delivery task."""
    delivery_id: UUID
    driver_id: UUID
    status: DeliveryStatus
    message: str


class VerifyPickupRequest(BaseModel):
    """Driver submits 6-digit OTP received from donor at pickup location."""
    pickup_otp: str = Field(
        ..., min_length=6, max_length=6, pattern=r"^[0-9]{6}$", description="6-digit pickup OTP"
    )
    proof_of_pickup_url: Optional[str] = Field(
        None, description="Optional photo URL confirming items received"
    )
    current_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    current_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class VerifyPickupResponse(BaseModel):
    """Result of successful donor pickup handshake."""
    delivery_id: UUID
    status: DeliveryStatus
    picked_up_at: datetime
    proof_of_pickup_url: Optional[str] = None
    message: str


class VerifyDropoffRequest(BaseModel):
    """Driver submits 6-digit OTP received from NGO + mandatory photo proof."""
    dropoff_otp: str = Field(
        ..., min_length=6, max_length=6, pattern=r"^[0-9]{6}$", description="6-digit dropoff OTP"
    )
    proof_of_delivery_url: str = Field(
        ..., min_length=5, description="Mandatory photo URL proving handover to NGO staff"
    )
    current_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    current_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    notes: Optional[str] = Field(None, description="Driver delivery notes")


class VerifyDropoffResponse(BaseModel):
    """Result of successful NGO dropoff handshake."""
    delivery_id: UUID
    status: DeliveryStatus
    delivered_at: datetime
    proof_of_delivery_url: str
    message: str


class DriverLocationUpdate(BaseModel):
    """Driver GPS telemetry update."""
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    status: Optional[DeliveryStatus] = None


class DeliveryResponse(BaseModel):
    """Standard delivery summary view."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    donation_id: UUID
    destination_ngo_id: UUID
    driver_id: Optional[UUID] = None
    status: DeliveryStatus
    pickup_location: CoordinateField = None
    dropoff_location: CoordinateField = None
    current_driver_location: CoordinateField = None
    estimated_distance_km: Optional[Decimal] = None
    estimated_duration_mins: Optional[int] = None
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    proof_of_pickup_url: Optional[str] = None
    proof_of_delivery_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
