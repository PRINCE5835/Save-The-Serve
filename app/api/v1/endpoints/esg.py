"""ESG (Environmental, Social, Governance) & Waste Audit Metrics Router

Implements:
GET /esg/stats: Cumulative and donor-specific impact metrics:
- Total meals rescued
- Kg of organic waste diverted from landfills
- CO2 equivalent emissions saved (EPA WARM conversion factor)
- Total monetary aid distributed
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.delivery import Delivery
from app.models.donation import Donation
from app.models.enums import DeliveryStatus, DonationKind, DonationStatus, ItemCategory
from app.models.profile import Profile


class ESGStatsResponse(BaseModel):
    """Cumulative and donor-specific ESG impact report."""
    total_meals_rescued: int = Field(..., description="Total quantity of cooked food portions rescued")
    total_kg_waste_diverted: float = Field(..., description="Metric tonnes or kg of organic waste diverted from landfills")
    total_co2_offset_kg: float = Field(..., description="Estimated CO2 equivalent offsets in kg (EPA factor ~2.5 kg CO2e / kg waste)")
    total_deliveries_completed: int = Field(..., description="Total successfully delivered rescue runs")
    total_monetary_aid_distributed: float = Field(..., description="Total direct and earmarked monetary aid disbursed")
    total_donations_count: int = Field(..., description="Count of completed donation actions")
    currency: str = Field(default="USD", description="Default reporting currency")
    calculation_methodology: str = Field(
        default="EPA WARM standard: 0.45 kg organic waste diverted per meal; 2.5 kg CO2e reduction per kg food waste diverted.",
        description="Standard ESG carbon and waste conversion formula",
    )


router = APIRouter()


@router.get(
    "/stats",
    response_model=ESGStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="ESG Impact & Waste Audit Metrics",
    description="Calculates cumulative and user-specific environmental impact: meals rescued, kg waste diverted, and CO2 offsets.",
)
async def get_esg_stats(
    donor_id: Optional[UUID] = Query(None, description="Optional filter by donor UUID"),
    current_user: Optional[Profile] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ESGStatsResponse:
    """Aggregates food waste diversion, CO2 offsets, and humanitarian aid stats."""
    target_donor = donor_id or (current_user.id if current_user and current_user.role.value == "donor" and donor_id is None else None)

    food_query = select(Donation).where(
        Donation.category == ItemCategory.COOKED_FOOD,
        Donation.status.in_([DonationStatus.COMPLETED, DonationStatus.DELIVERED]),
    )
    if target_donor:
        food_query = food_query.where(Donation.donor_id == target_donor)

    food_results = (await db.execute(food_query)).scalars().all()
    total_meals = sum(int(d.quantity_amount) for d in food_results)

    kg_waste = round(total_meals * 0.45, 2)
    co2_offsets = round(kg_waste * 2.5, 2)

    deliv_query = select(func.count(Delivery.id)).where(Delivery.status == DeliveryStatus.DELIVERED)
    deliv_count = (await db.execute(deliv_query)).scalar() or len(food_results)

    monetary_query = select(Donation).where(
        Donation.kind.in_([DonationKind.MONETARY_DIRECT, DonationKind.MONETARY_EARMARKED]),
        Donation.status.in_([DonationStatus.COMPLETED, DonationStatus.DELIVERED]),
    )
    if target_donor:
        monetary_query = monetary_query.where(Donation.donor_id == target_donor)

    monetary_results = (await db.execute(monetary_query)).scalars().all()
    total_money = float(sum(d.quantity_amount for d in monetary_results))

    total_donations_count = len(food_results) + len(monetary_results)

    return ESGStatsResponse(
        total_meals_rescued=total_meals,
        total_kg_waste_diverted=kg_waste,
        total_co2_offset_kg=co2_offsets,
        total_deliveries_completed=deliv_count,
        total_monetary_aid_distributed=total_money,
        total_donations_count=total_donations_count,
        currency="USD",
    )
