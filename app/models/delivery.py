"""Delivery Logistics ORM Model"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List
from geoalchemy2 import Geography
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import DeliveryStatus

if TYPE_CHECKING:
    from app.models.profile import Profile
    from app.models.ngo import NGODetail
    from app.models.donation import Donation
    from app.models.support import SupportTicket


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    donation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("donations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    driver_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    destination_ngo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ngo_details.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[DeliveryStatus] = mapped_column(
        ENUM(DeliveryStatus, name="delivery_status", create_type=False),
        nullable=False,
        default=DeliveryStatus.ASSIGNED,
        index=True,
    )
    pickup_location: Mapped[Geography] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    dropoff_location: Mapped[Geography] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    current_driver_location: Mapped[Optional[Geography]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    proof_of_pickup_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proof_of_delivery_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pickup_otp_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_otp_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    estimated_distance_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    estimated_duration_mins: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    picked_up_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    donation: Mapped["Donation"] = relationship("Donation", back_populates="delivery")
    driver: Mapped[Optional["Profile"]] = relationship("Profile", back_populates="deliveries_driven")
    destination_ngo: Mapped["NGODetail"] = relationship("NGODetail", back_populates="received_deliveries")
    support_tickets: Mapped[List["SupportTicket"]] = relationship(
        "SupportTicket", back_populates="related_delivery"
    )
