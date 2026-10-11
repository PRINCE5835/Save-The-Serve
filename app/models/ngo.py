"""NGO Details ORM Model"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List, Any
from geoalchemy2 import Geography
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.profile import Profile
    from app.models.donation import Donation
    from app.models.delivery import Delivery


class NGODetail(Base):
    __tablename__ = "ngo_details"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tax_exemption_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    operating_radius_km: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("25.00"), nullable=False
    )
    hq_location: Mapped[Geography] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    website_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(25), nullable=False)
    capacity_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_documents: Mapped[Optional[Any]] = mapped_column(
        JSONB, default=list, nullable=True
    )
    bank_account_info: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    profile: Mapped["Profile"] = relationship("Profile", back_populates="ngo_details")
    assigned_donations: Mapped[List["Donation"]] = relationship(
        "Donation", back_populates="assigned_ngo"
    )
    received_deliveries: Mapped[List["Delivery"]] = relationship(
        "Delivery", back_populates="destination_ngo"
    )
