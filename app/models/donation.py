"""Donation ORM Model"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List, Any
from geoalchemy2 import Geography
from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import DonationKind, DonationStatus, ItemCategory

if TYPE_CHECKING:
    from app.models.profile import Profile
    from app.models.ngo import NGODetail
    from app.models.delivery import Delivery
    from app.models.support import SupportTicket


class Donation(Base):
    __tablename__ = "donations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    donor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_ngo_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ngo_details.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    kind: Mapped[DonationKind] = mapped_column(
        ENUM(DonationKind, name="donation_kind", create_type=False),
        nullable=False,
        default=DonationKind.PHYSICAL_ITEM,
    )
    category: Mapped[Optional[ItemCategory]] = mapped_column(
        ENUM(ItemCategory, name="item_category", create_type=False),
        nullable=True,
    )
    status: Mapped[DonationStatus] = mapped_column(
        ENUM(DonationStatus, name="donation_status", create_type=False),
        nullable=False,
        default=DonationStatus.PENDING,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quantity_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    monetary_currency: Mapped[Optional[str]] = mapped_column(String(3), default="USD", nullable=True)
    earmarked_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pickup_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pickup_location: Mapped[Optional[Geography]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    pickup_window_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    pickup_window_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_perishable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prepared_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expiry_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    reserved_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    dietary_tags: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(Text), default=list, nullable=True
    )
    image_urls: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(Text), default=list, nullable=True
    )
    metadata_json: Mapped[Optional[Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    donor: Mapped["Profile"] = relationship("Profile", back_populates="donations_created")
    assigned_ngo: Mapped[Optional["NGODetail"]] = relationship(
        "NGODetail", back_populates="assigned_donations"
    )
    delivery: Mapped[Optional["Delivery"]] = relationship(
        "Delivery", back_populates="donation", uselist=False, cascade="all, delete-orphan"
    )
    support_tickets: Mapped[List["SupportTicket"]] = relationship(
        "SupportTicket", back_populates="related_donation"
    )
