"""Geospatial Matching Engine for Save The Serve (S.T.S)

Executes optimized PostGIS radius queries using ST_DWithin and ST_Distance
over indexed geography points to discover available donations near an NGO or driver.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from geoalchemy2 import Geography
from sqlalchemy import and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.donation import Donation
from app.models.enums import DonationKind, DonationStatus, ItemCategory


@dataclass
class MatchedDonation:
    """Encapsulates a matched donation record along with calculated spatial metrics."""
    donation: Donation
    distance_km: float
    urgency_level: str
    is_claimable: bool


def calculate_urgency_level(
    is_perishable: bool, expiry_time: Optional[datetime], now_dt: datetime
) -> str:
    """Calculates food salvage urgency based on time remaining until expiry.

    - critical: < 3 hours remaining before spoiling
    - high: < 6 hours remaining
    - normal: > 6 hours remaining or non-perishable goods
    """
    if not is_perishable or not expiry_time:
        return "normal"

    if expiry_time.tzinfo is None:
        expiry_time = expiry_time.replace(tzinfo=timezone.utc)

    remaining = expiry_time - now_dt
    if remaining <= timedelta(hours=3):
        return "critical"
    if remaining <= timedelta(hours=6):
        return "high"
    return "normal"


async def find_nearby_donations(
    db: AsyncSession,
    center_latitude: float,
    center_longitude: float,
    radius_km: float = 25.0,
    category: Optional[ItemCategory] = None,
    kind: Optional[DonationKind] = None,
    urgency_filter: Optional[str] = None,
    limit: int = 50,
) -> List[MatchedDonation]:
    """Queries open, unexpired donations within a custom kilometer radius.

    Uses PostGIS spatial operators:
    - ST_MakePoint & ST_SetSRID: Constructs WGS84 point.
    - ST_DWithin: Filters bounding radius using GIST spatial index in sub-milliseconds.
    - ST_Distance: Calculates geodesic ellipsoidal distance in meters.

    Args:
        db: Active AsyncSession.
        center_latitude: Query origin latitude [-90.0, 90.0].
        center_longitude: Query origin longitude [-180.0, 180.0].
        radius_km: Search radius in kilometers.
        category: Optional ItemCategory filter.
        kind: Optional DonationKind filter.
        urgency_filter: Optional filter ('critical', 'high', 'normal').
        limit: Max records to return.

    Returns:
        List of MatchedDonation objects sorted by nearest distance ascending.
    """
    radius_meters = float(radius_km) * 1000.0
    now = datetime.now(timezone.utc)

    center_point_geog = cast(
        func.ST_SetSRID(func.ST_MakePoint(center_longitude, center_latitude), 4326),
        Geography,
    )

    distance_meters_expr = func.ST_Distance(
        Donation.pickup_location, center_point_geog
    ).label("distance_meters")

    query = (
        select(Donation, distance_meters_expr)
        .options(selectinload(Donation.donor), selectinload(Donation.assigned_ngo))
        .where(Donation.pickup_location.isnot(None))
    )

    query = query.where(
        func.ST_DWithin(Donation.pickup_location, center_point_geog, radius_meters)
    )

    is_available_cond = Donation.status == DonationStatus.AVAILABLE
    is_expired_reservation = and_(
        Donation.status == DonationStatus.RESERVED,
        Donation.reserved_until.isnot(None),
        Donation.reserved_until < now,
    )
    query = query.where(or_(is_available_cond, is_expired_reservation))

    is_not_expired = or_(
        Donation.expiry_time.is_(None),
        Donation.expiry_time > now,
    )
    query = query.where(is_not_expired)

    if category is not None:
        query = query.where(Donation.category == category)

    if kind is not None:
        query = query.where(Donation.kind == kind)

    if urgency_filter:
        urg_f = urgency_filter.lower().strip()
        if urg_f == "critical":
            query = query.where(
                and_(
                    Donation.is_perishable.is_(True),
                    Donation.expiry_time.isnot(None),
                    Donation.expiry_time <= now + timedelta(hours=3),
                )
            )
        elif urg_f == "high":
            query = query.where(
                and_(
                    Donation.is_perishable.is_(True),
                    Donation.expiry_time.isnot(None),
                    Donation.expiry_time > now + timedelta(hours=3),
                    Donation.expiry_time <= now + timedelta(hours=6),
                )
            )
        elif urg_f == "normal":
            query = query.where(
                or_(
                    Donation.is_perishable.is_(False),
                    Donation.expiry_time.is_(None),
                    Donation.expiry_time > now + timedelta(hours=6),
                )
            )

    query = query.order_by(distance_meters_expr.asc()).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    matched: List[MatchedDonation] = []
    for donation_row, dist_meters in rows:
        distance_km = round(float(dist_meters) / 1000.0, 2)
        urgency = calculate_urgency_level(
            is_perishable=donation_row.is_perishable,
            expiry_time=donation_row.expiry_time,
            now_dt=now,
        )

        if urgency_filter and urgency != urgency_filter.lower():
            continue

        claimable = (
            donation_row.status == DonationStatus.AVAILABLE
            or (
                donation_row.status == DonationStatus.RESERVED
                and donation_row.reserved_until is not None
                and donation_row.reserved_until < now
            )
        )

        matched.append(
            MatchedDonation(
                donation=donation_row,
                distance_km=distance_km,
                urgency_level=urgency,
                is_claimable=claimable,
            )
        )

    return matched
