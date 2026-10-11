"""Customer Support, Help Desk & Dispute Resolution Endpoints for Save The Serve (S.T.S)

Implements:
1. POST /support/tickets: File a help desk or emergency escalation ticket.
2. GET /support/tickets: List user's tickets (or all tickets for admins/agents).
3. GET /support/tickets/{id}: Detailed ticket review.
4. PATCH /support/tickets/{id}: Admin or support agent updates status and resolution notes.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_any_role, require_role
from app.models.delivery import Delivery
from app.models.donation import Donation
from app.models.enums import TicketPriority, TicketStatus, UserRole
from app.models.profile import Profile
from app.models.support import SupportTicket
from app.schemas.support import TicketCreate, TicketResponse, TicketStatusUpdate

router = APIRouter()


def _format_ticket_response(ticket: SupportTicket) -> TicketResponse:
    now_dt = datetime.now(timezone.utc)
    return TicketResponse(
        id=ticket.id,
        creator_id=ticket.creator_id,
        assigned_agent_id=ticket.assigned_agent_id,
        related_donation_id=ticket.related_donation_id,
        related_delivery_id=ticket.related_delivery_id,
        subject=ticket.subject,
        message=ticket.message,
        priority=ticket.priority,
        status=ticket.status,
        resolution_notes=ticket.resolution_notes,
        created_at=ticket.created_at or now_dt,
        updated_at=ticket.updated_at or now_dt,
    )


@router.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Support Ticket",
    description="File a customer support, dispute, or emergency escalation ticket.",
)
async def create_support_ticket(
    payload: TicketCreate = Body(...),
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    """Creates a new support ticket linked to current user."""
    if payload.related_donation_id is not None:
        don_q = select(Donation).where(Donation.id == payload.related_donation_id)
        donation = (await db.execute(don_q)).scalar_one_or_none()
        if not donation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Related donation '{payload.related_donation_id}' was not found.",
            )

    if payload.related_delivery_id is not None:
        del_q = select(Delivery).where(Delivery.id == payload.related_delivery_id)
        delivery = (await db.execute(del_q)).scalar_one_or_none()
        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Related delivery '{payload.related_delivery_id}' was not found.",
            )

    now = datetime.now(timezone.utc)
    ticket_id = uuid.uuid4()
    ticket = SupportTicket(
        id=ticket_id,
        creator_id=current_user.id,
        related_donation_id=payload.related_donation_id,
        related_delivery_id=payload.related_delivery_id,
        subject=payload.subject.strip(),
        message=payload.message.strip(),
        priority=payload.priority,
        status=TicketStatus.OPEN,
        created_at=now,
        updated_at=now,
    )
    db.add(ticket)
    await db.flush()

    return _format_ticket_response(ticket)


@router.get(
    "/tickets",
    response_model=List[TicketResponse],
    summary="List Support Tickets",
    description="Users view tickets they created; administrators and agents view all tickets.",
)
async def list_support_tickets(
    ticket_status: Optional[TicketStatus] = Query(None, alias="status"),
    priority: Optional[TicketPriority] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[TicketResponse]:
    """Lists support tickets filtered by user permissions."""
    query = select(SupportTicket).limit(limit)

    if current_user.role != UserRole.ADMIN:
        query = query.where(SupportTicket.creator_id == current_user.id)

    if ticket_status is not None:
        query = query.where(SupportTicket.status == ticket_status)
    if priority is not None:
        query = query.where(SupportTicket.priority == priority)

    query = query.order_by(SupportTicket.created_at.desc())
    res = await db.execute(query)
    tickets = res.scalars().all()
    return [_format_ticket_response(t) for t in tickets]


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    summary="Get Ticket Details",
)
async def get_support_ticket(
    ticket_id: uuid.UUID,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    """Retrieves full details of a support ticket."""
    query = select(SupportTicket).where(SupportTicket.id == ticket_id)
    ticket = (await db.execute(query)).scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Support ticket '{ticket_id}' was not found.",
        )

    if current_user.role != UserRole.ADMIN and ticket.creator_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return _format_ticket_response(ticket)


@router.patch(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    summary="Update Ticket Status & Resolution",
    description="Admin or support agent advances ticket status or adds resolution notes.",
)
async def update_support_ticket(
    ticket_id: uuid.UUID,
    payload: TicketStatusUpdate = Body(...),
    current_user: Profile = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    """Updates ticket status and appends resolution notes."""
    query = select(SupportTicket).where(SupportTicket.id == ticket_id)
    ticket = (await db.execute(query)).scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Support ticket '{ticket_id}' was not found.",
        )

    ticket.status = payload.status
    if payload.resolution_notes:
        ticket.resolution_notes = payload.resolution_notes.strip()
    ticket.assigned_agent_id = current_user.id
    ticket.updated_at = datetime.now(timezone.utc)

    await db.flush()
    return _format_ticket_response(ticket)
