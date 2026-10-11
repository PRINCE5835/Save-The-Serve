"""User Profile ORM Model"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, List
from geoalchemy2 import Geography
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.ngo import NGODetail
    from app.models.donation import Donation
    from app.models.delivery import Delivery
    from app.models.support import SupportTicket


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role: Mapped[UserRole] = mapped_column(
        ENUM(UserRole, name="user_role", create_type=False),
        nullable=False,
        default=UserRole.DONOR,
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(25), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address_line: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[Geography]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    ngo_details: Mapped[Optional["NGODetail"]] = relationship(
        "NGODetail", back_populates="profile", uselist=False, cascade="all, delete-orphan"
    )
    donations_created: Mapped[List["Donation"]] = relationship(
        "Donation", back_populates="donor", foreign_keys="Donation.donor_id"
    )
    deliveries_driven: Mapped[List["Delivery"]] = relationship(
        "Delivery", back_populates="driver", foreign_keys="Delivery.driver_id"
    )
    tickets_created: Mapped[List["SupportTicket"]] = relationship(
        "SupportTicket", back_populates="creator", foreign_keys="SupportTicket.creator_id"
    )
