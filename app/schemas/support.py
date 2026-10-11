"""Pydantic v2 Schemas for Support Tickets, User Profile Settings, Passwords & Notifications"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TicketPriority, TicketStatus
from app.schemas.profile import CoordinateSchema, ProfileResponse


class TicketCreate(BaseModel):
    """Payload to file a new help desk or emergency support ticket."""
    subject: str = Field(..., min_length=3, max_length=255, description="Brief summary of the issue")
    message: str = Field(..., min_length=10, description="Detailed explanation of the issue or dispute")
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM, description="low, medium, high, or urgent")
    related_donation_id: Optional[UUID] = Field(None, description="Optional associated donation UUID")
    related_delivery_id: Optional[UUID] = Field(None, description="Optional associated delivery UUID")


class TicketStatusUpdate(BaseModel):
    """Payload for support agents or admins to resolve or advance a ticket."""
    status: TicketStatus = Field(..., description="open, in_progress, resolved, or closed")
    resolution_notes: Optional[str] = Field(None, description="Explanatory notes upon resolution")


class TicketResponse(BaseModel):
    """Full detail view of a support ticket."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    creator_id: UUID
    assigned_agent_id: Optional[UUID] = None
    related_donation_id: Optional[UUID] = None
    related_delivery_id: Optional[UUID] = None
    subject: str
    message: str
    priority: TicketPriority
    status: TicketStatus
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PasswordChangeRequest(BaseModel):
    """Payload to securely change user account password."""
    current_password: str = Field(..., min_length=6, description="Existing account password for verification")
    new_password: str = Field(..., min_length=8, max_length=100, description="New strong password (min 8 characters)")


class PasswordChangeResponse(BaseModel):
    message: str
    updated_at: datetime


class NotificationPreferences(BaseModel):
    """User toggles for mobile push notifications, emails, and emergency surplus alerts."""
    push_enabled: bool = Field(default=True, description="Master push notification toggle")
    email_enabled: bool = Field(default=True, description="Email alerts toggle")
    sms_alerts_enabled: bool = Field(default=False, description="Urgent SMS alerts toggle")
    urgent_surplus_alerts: bool = Field(default=True, description="High-priority alerts for food nearing expiry (< 2h)")
    fcm_device_token: Optional[str] = Field(None, description="Firebase Cloud Messaging device push token")


class NotificationPreferencesResponse(NotificationPreferences):
    """Current user notification settings."""
    user_id: UUID
    updated_at: datetime
