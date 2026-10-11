"""Background Perishable Food Watchdog & Dynamic Escalation Service

Monitors unreserved cooked meals and perishable donations in Save The Serve (S.T.S).
Implements:
1. Dynamic Escalation:
   - When surplus cooked food reaches < 2 hours before spoiling, automatically:
     a) Flags status as CRITICAL_URGENCY in metadata.
     b) Auto-expands the matching radius (e.g., from default 25km to 50km+).
     c) Locates nearby approved NGOs and drivers in the expanded zone for rapid salvage dispatch.
2. Auto-Expiration:
   - When food passes its expiry deadline (expiry_time <= now), marks status as EXPIRED.
3. Background Worker:
   - Async watchdog loop with configurable polling intervals, lifespan integration, and manual trigger support.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Set
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import async_session_factory
from app.models.donation import Donation
from app.models.enums import DonationKind, DonationStatus, ItemCategory
from app.models.ngo import NGODetail

logger = logging.getLogger("sts.expiry_monitor")


@dataclass
class EscalationEvent:
    """Details of a donation undergoing critical urgency expansion."""
    donation_id: UUID
    title: str
    minutes_remaining: int
    original_radius_km: float
    expanded_radius_km: float
    nearby_ngos_count: int
    nearby_ngo_names: List[str] = field(default_factory=list)


@dataclass
class ExpiryScanReport:
    """Consolidated summary of a watchdog scan execution."""
    scanned_at: datetime
    expired_count: int
    escalated_count: int
    expired_donation_ids: List[UUID] = field(default_factory=list)
    escalations: List[EscalationEvent] = field(default_factory=list)


async def scan_and_escalate_perishables(
    db: AsyncSession,
    critical_threshold_hours: float = 2.0,
    radius_multiplier: float = 2.0,
) -> ExpiryScanReport:
    """Scans for open perishable food, expires spoiled meals, and applies dynamic radius escalation.

    Args:
        db: Active AsyncSession.
        critical_threshold_hours: Time remaining in hours to trigger critical escalation (default 2.0).
        radius_multiplier: Multiplier to expand search radius (default 2x).

    Returns:
        ExpiryScanReport with metrics and details.
    """
    now = datetime.now(timezone.utc)
    critical_deadline = now + timedelta(hours=critical_threshold_hours)

    report = ExpiryScanReport(
        scanned_at=now,
        expired_count=0,
        escalated_count=0,
    )

    is_available_cond = Donation.status == DonationStatus.AVAILABLE
    is_expired_lock = and_(
        Donation.status == DonationStatus.RESERVED,
        Donation.reserved_until.isnot(None),
        Donation.reserved_until < now,
    )

    query = (
        select(Donation)
        .where(
            or_(
                Donation.category == ItemCategory.COOKED_FOOD,
                Donation.is_perishable.is_(True),
            ),
            Donation.expiry_time.isnot(None),
            Donation.status != DonationStatus.EXPIRED,
            Donation.status != DonationStatus.COMPLETED,
            Donation.status != DonationStatus.DELIVERED,
            Donation.status != DonationStatus.CANCELLED,
            or_(is_available_cond, is_expired_lock),
        )
    )

    result = await db.execute(query)
    donations: List[Donation] = result.scalars().all()

    for donation in donations:
        exp_time = (
            donation.expiry_time
            if donation.expiry_time.tzinfo
            else donation.expiry_time.replace(tzinfo=timezone.utc)
        )

        metadata = dict(donation.metadata_json or {})

        if exp_time <= now:
            donation.status = DonationStatus.EXPIRED
            metadata["expired_by_watchdog_at"] = now.isoformat()
            metadata["urgency_status"] = "EXPIRED"
            donation.metadata_json = metadata
            report.expired_count += 1
            report.expired_donation_ids.append(donation.id)
            logger.warning(
                f"[Expiry Watchdog] Donation '{donation.title}' ({donation.id}) expired at {exp_time.isoformat()}."
            )
            continue

        if now < exp_time <= critical_deadline:
            remaining_mins = max(1, int((exp_time - now).total_seconds() / 60))
            orig_radius = float(metadata.get("search_radius_km", settings.DEFAULT_SEARCH_RADIUS_KM))
            expanded_radius = min(
                orig_radius * radius_multiplier,
                float(settings.MAX_SEARCH_RADIUS_KM),
            )

            metadata["urgency_status"] = "CRITICAL_URGENCY"
            metadata["is_escalated"] = True
            metadata["escalated_at"] = now.isoformat()
            metadata["expanded_radius_km"] = expanded_radius
            metadata["minutes_remaining"] = remaining_mins
            donation.metadata_json = metadata

            nearby_ngo_names: List[str] = []
            if donation.pickup_location is not None:
                expanded_meters = expanded_radius * 1000.0
                ngo_query = (
                    select(NGODetail.organization_name)
                    .where(
                        NGODetail.is_approved.is_(True),
                        func.ST_DWithin(
                            NGODetail.hq_location,
                            donation.pickup_location,
                            expanded_meters,
                        ),
                    )
                    .limit(10)
                )
                ngo_res = await db.execute(ngo_query)
                nearby_ngo_names = list(ngo_res.scalars().all())

            metadata["nearby_notified_ngos_count"] = len(nearby_ngo_names)
            donation.metadata_json = metadata

            escalation_ev = EscalationEvent(
                donation_id=donation.id,
                title=donation.title,
                minutes_remaining=remaining_mins,
                original_radius_km=orig_radius,
                expanded_radius_km=expanded_radius,
                nearby_ngos_count=len(nearby_ngo_names),
                nearby_ngo_names=nearby_ngo_names,
            )
            report.escalated_count += 1
            report.escalations.append(escalation_ev)

            logger.info(
                f"[Expiry Watchdog Escalation] '{donation.title}' has {remaining_mins}m remaining. "
                f"Expanded search radius from {orig_radius}km to {expanded_radius}km. "
                f"Found {len(nearby_ngo_names)} nearby NGOs."
            )

    await db.flush()
    return report


class ExpiryWatchdog:
    """Asynchronous background worker polling unreserved surplus food."""

    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval_seconds = check_interval_seconds
        self._is_running = False
        self._task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def start(self) -> None:
        """Starts the background monitoring loop."""
        if self._is_running:
            return
        self._is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"[Expiry Watchdog] Background worker started (interval: {self.check_interval_seconds}s).")

    async def stop(self) -> None:
        """Stops the background monitoring loop."""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("[Expiry Watchdog] Background worker stopped.")

    async def _run_loop(self) -> None:
        """Internal continuous loop."""
        while self._is_running:
            try:
                async with async_session_factory() as session:
                    report = await scan_and_escalate_perishables(session)
                    await session.commit()
                    if report.expired_count > 0 or report.escalated_count > 0:
                        logger.info(
                            f"[Expiry Watchdog Run] Expired: {report.expired_count}, "
                            f"Escalated (Critical Urgency): {report.escalated_count}."
                        )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Expiry Watchdog Error] Execution failed: {e}", exc_info=True)

            try:
                await asyncio.sleep(self.check_interval_seconds)
            except asyncio.CancelledError:
                break


expiry_watchdog = ExpiryWatchdog(check_interval_seconds=60)
