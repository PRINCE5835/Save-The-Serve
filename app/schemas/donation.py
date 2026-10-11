"""Pydantic v2 Schemas for Complete Donation Lifecycle

Validates:
- Physical Donations (perishable food with prepared_at/expires_at, groceries, clothes, blankets, medical, other)
- Direct Monetary Donations (amount, currency, target NGO)
- Earmarked Monetary Donations (item name e.g. '50 Blankets', cost per unit, units funded, target NGO)
- Feed Filtering & Claim Locks
- Escrow Intent Transactions
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from uuid import UUID
from pydantic import BaseModel, BeforeValidator, ConfigDict, Discriminator, Field, Tag, model_validator

from app.core.database import parse_geography_point
from app.models.enums import DonationKind, DonationStatus, ItemCategory
from app.schemas.profile import CoordinateSchema


def convert_geography_to_coordinate(v: Any) -> Any:
    """Converts WKTElement, WKBElement, Point, or string to CoordinateSchema."""
    if v is None:
        return None
    if isinstance(v, CoordinateSchema):
        return v
    if isinstance(v, dict):
        return v
    pt = parse_geography_point(v)
    if pt:
        return {"longitude": pt[0], "latitude": pt[1]}
    return v


CoordinateField = Annotated[CoordinateSchema, BeforeValidator(convert_geography_to_coordinate)]


class PhysicalDonationCreate(BaseModel):
    """Payload for donating physical goods (perishable food, groceries, clothes, blankets, medical, or other)."""
    kind: Literal[DonationKind.PHYSICAL_ITEM] = DonationKind.PHYSICAL_ITEM
    category: ItemCategory = Field(
        ...,
        description="Category: cooked_food, grocery, clothes, blanket, medical, or other",
    )
    title: str = Field(..., min_length=3, max_length=255, description="Clear, descriptive item title")
    description: Optional[str] = Field(None, description="Detailed item breakdown, condition, allergen info")
    custom_category_note: Optional[str] = Field(
        None,
        description="Required explanation if category is 'other' (e.g. hygiene kits, custom equipment)",
    )
    custom_text: Optional[str] = Field(
        None,
        description="Alternative alias for custom_category_note for custom text donations",
    )
    quantity_amount: Decimal = Field(..., gt=0, description="Quantity numerical magnitude")
    quantity_unit: str = Field(..., min_length=1, max_length=50, description="Unit (e.g., servings, kg, boxes, units)")
    pickup_address: str = Field(..., min_length=5, description="Street address for driver dispatch")
    pickup_location: CoordinateSchema = Field(..., description="PostGIS coordinates for proximity matching")
    pickup_window_start: Optional[datetime] = Field(None, description="Earliest available pickup timestamp")
    pickup_window_end: Optional[datetime] = Field(None, description="Latest pickup timestamp")
    is_perishable: bool = Field(default=False, description="Flag for cooked meals and perishable fresh produce")
    prepared_at: Optional[datetime] = Field(None, description="Preparation/cooking time for cooked meals")
    expires_at: Optional[datetime] = Field(None, description="Expiration deadline before food spoils")
    dietary_tags: Optional[List[str]] = Field(default_factory=list, description="e.g., ['vegetarian', 'halal', 'nut-free']")
    image_urls: Optional[List[str]] = Field(default_factory=list, description="Proof or visual inspection images")

    @model_validator(mode="after")
    def validate_physical_rules(self) -> "PhysicalDonationCreate":
        if self.category == ItemCategory.COOKED_FOOD:
            self.is_perishable = True

        if self.is_perishable:
            if not self.expires_at:
                raise ValueError("Perishable donations require an explicit 'expires_at' deadline.")
            if self.prepared_at and self.expires_at <= self.prepared_at:
                raise ValueError("'expires_at' must be subsequent to 'prepared_at'.")

        if not self.custom_category_note and self.custom_text:
            self.custom_category_note = self.custom_text

        if self.category == ItemCategory.OTHER and not (self.description or self.custom_category_note):
            raise ValueError("When category is 'other', please provide a description or custom_category_note.")

        if self.pickup_window_start and self.pickup_window_end:
            if self.pickup_window_end < self.pickup_window_start:
                raise ValueError("'pickup_window_end' must be after 'pickup_window_start'.")

        return self


class DirectMonetaryDonationCreate(BaseModel):
    """Payload for direct monetary relief directed to a specific verified NGO."""
    kind: Literal[DonationKind.MONETARY_DIRECT] = DonationKind.MONETARY_DIRECT
    amount: Decimal = Field(..., gt=0, description="Contribution amount")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="ISO 4217 Currency Code (e.g. USD, EUR, INR)")
    target_ngo_id: UUID = Field(..., description="ID of the recipient Non-Profit Organization")
    title: Optional[str] = Field("Direct NGO Relief Contribution", max_length=255)
    donor_note: Optional[str] = Field(None, description="Optional public or private message from donor")
    payment_method_id: Optional[str] = Field(None, description="Stripe/Razorpay payment method token")


class EarmarkedMonetaryDonationCreate(BaseModel):
    """Payload for earmarked funding tied to specific relief items (e.g., '50 Blankets')."""
    kind: Literal[DonationKind.MONETARY_EARMARKED] = DonationKind.MONETARY_EARMARKED
    item_name: str = Field(..., min_length=2, max_length=255, description="Item name (e.g., '50 Blankets', 'First Aid Kits')")
    cost_per_unit: Decimal = Field(..., gt=0, description="Price per individual unit")
    total_amount_funded: Decimal = Field(..., gt=0, description="Total monetary pledge")
    units_count: Optional[int] = Field(None, gt=0, description="Total units being sponsored (calculated if omitted)")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    target_ngo_id: UUID = Field(..., description="Target NGO purchasing and distributing the supplies")
    donor_note: Optional[str] = Field(None, description="Message to the community or volunteers")

    @model_validator(mode="after")
    def validate_earmarked_math(self) -> "EarmarkedMonetaryDonationCreate":
        if self.units_count is None:
            computed = self.total_amount_funded / self.cost_per_unit
            if abs(computed - round(computed)) > Decimal("0.01"):
                raise ValueError(
                    f"total_amount_funded ({self.total_amount_funded}) must be an exact multiple of "
                    f"cost_per_unit ({self.cost_per_unit}) when units_count is not explicitly provided."
                )
            self.units_count = int(round(computed))
        else:
            expected_total = self.cost_per_unit * Decimal(self.units_count)
            if abs(self.total_amount_funded - expected_total) > Decimal("0.05"):
                raise ValueError(
                    f"total_amount_funded ({self.total_amount_funded}) does not match "
                    f"units_count * cost_per_unit ({self.units_count} * {self.cost_per_unit} = {expected_total})."
                )
        return self


def determine_donation_kind(v: Any) -> str:
    """Intelligently detects donation kind from payload fields or explicit 'kind'."""
    if isinstance(v, dict):
        kind = v.get("kind")
        if kind:
            return kind.value if hasattr(kind, "value") else str(kind)
        if "item_name" in v or "earmarked_cause" in v or "cost_per_unit" in v:
            return DonationKind.MONETARY_EARMARKED.value
        if "amount" in v:
            return DonationKind.MONETARY_DIRECT.value
        return DonationKind.PHYSICAL_ITEM.value
    kind_attr = getattr(v, "kind", None)
    if kind_attr:
        return kind_attr.value if hasattr(kind_attr, "value") else str(kind_attr)
    return DonationKind.PHYSICAL_ITEM.value


DonationCreateRequest = Annotated[
    Union[
        Annotated[PhysicalDonationCreate, Tag(DonationKind.PHYSICAL_ITEM.value)],
        Annotated[DirectMonetaryDonationCreate, Tag(DonationKind.MONETARY_DIRECT.value)],
        Annotated[EarmarkedMonetaryDonationCreate, Tag(DonationKind.MONETARY_EARMARKED.value)],
    ],
    Discriminator(determine_donation_kind),
]


class DonationResponse(BaseModel):
    """Full detail view of an individual donation."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    donor_id: UUID
    assigned_ngo_id: Optional[UUID] = None
    kind: DonationKind
    category: Optional[ItemCategory] = None
    status: DonationStatus
    title: str
    description: Optional[str] = None
    quantity_amount: Decimal
    quantity_unit: Optional[str] = None
    monetary_currency: Optional[str] = None
    earmarked_cause: Optional[str] = None
    pickup_address: Optional[str] = None
    pickup_location: Optional[CoordinateField] = None
    pickup_window_start: Optional[datetime] = None
    pickup_window_end: Optional[datetime] = None
    is_perishable: bool
    prepared_at: Optional[datetime] = None
    expiry_time: Optional[datetime] = None
    reserved_until: Optional[datetime] = None
    dietary_tags: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None
    metadata_json: Optional[Any] = None
    created_at: datetime
    updated_at: datetime


class DonationFeedItem(DonationResponse):
    """Enriched donation object within geospatial discovery feed."""
    distance_km: float = Field(..., description="Geodesic distance from query center in kilometers")
    urgency_level: str = Field(..., description="'critical' (< 3h remaining), 'high' (< 6h), or 'normal'")
    is_claimable: bool = Field(..., description="True if currently available for reservation")


class ClaimDonationResponse(BaseModel):
    """Result of claiming an available donation with a 15-minute lock."""
    donation_id: UUID
    assigned_ngo_id: UUID
    status: DonationStatus
    reserved_until: datetime
    reservation_lock_minutes: int = 15
    message: str


class EarmarkedFundRequest(BaseModel):
    """Payload for creating an escrow purchasing intent for essential items."""
    item_name: str = Field(..., min_length=2, max_length=255, description="Item name (e.g. '50 Blankets')")
    cost_per_unit: Decimal = Field(..., gt=0, description="Cost per individual unit")
    total_amount_funded: Decimal = Field(..., gt=0, description="Total amount to be deposited in escrow")
    units_count: Optional[int] = Field(None, gt=0, description="Number of items to fund (calculated if omitted)")
    target_ngo_id: UUID = Field(..., description="Recipient NGO fulfilling procurement")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    donor_note: Optional[str] = None

    @model_validator(mode="after")
    def validate_escrow_totals(self) -> "EarmarkedFundRequest":
        if self.units_count is None:
            computed = self.total_amount_funded / self.cost_per_unit
            if abs(computed - round(computed)) > Decimal("0.01"):
                raise ValueError(
                    f"total_amount_funded ({self.total_amount_funded}) must be an exact multiple of "
                    f"cost_per_unit ({self.cost_per_unit}) when units_count is not explicitly provided."
                )
            self.units_count = int(round(computed))
        else:
            expected = self.cost_per_unit * Decimal(self.units_count)
            if abs(self.total_amount_funded - expected) > Decimal("0.05"):
                raise ValueError(
                    f"total_amount_funded ({self.total_amount_funded}) must equal "
                    f"units_count * cost_per_unit ({expected})."
                )
        return self


class EscrowIntentResponse(BaseModel):
    """Payment gateway client secret and escrow transaction reservation."""
    escrow_transaction_id: UUID
    donation_id: UUID
    target_ngo_id: UUID
    item_name: str
    units_count: int
    cost_per_unit: Decimal
    total_amount: Decimal
    currency: str
    client_secret: str
    escrow_status: str
    message: str


class PaymentConfirmRequest(BaseModel):
    """Payment verification payload submitted after checkout / webhook."""
    payment_intent_id: Optional[str] = Field(default=None, description="Stripe/Razorpay payment transaction ID")
    payment_status: str = Field(default="succeeded", description="Payment status: 'succeeded', 'paid', or 'failed'")
    payment_method: Optional[str] = Field(default="card", description="Payment method used (e.g. card, upi, bank_transfer)")


class PaymentConfirmResponse(BaseModel):
    """Confirmation response upon successful escrow payment settlement."""
    donation_id: UUID
    status: DonationStatus
    escrow_status: str
    total_amount: Decimal
    currency: str
    target_ngo_id: Optional[UUID] = None
    payment_id: str
    confirmed_at: datetime
    message: str
