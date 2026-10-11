"""Enumerated types for Save The Serve (S.T.S) Data Models

Maps 1-to-1 to PostgreSQL ENUM definitions in the migration script.
"""

from enum import Enum


class UserRole(str, Enum):
    DONOR = "donor"
    NGO = "ngo"
    DRIVER = "driver"
    ADMIN = "admin"


class DonationKind(str, Enum):
    PHYSICAL_ITEM = "physical_item"
    MONETARY_DIRECT = "monetary_direct"
    MONETARY_EARMARKED = "monetary_earmarked"


class ItemCategory(str, Enum):
    COOKED_FOOD = "cooked_food"
    GROCERY = "grocery"
    CLOTHES = "clothes"
    BLANKET = "blanket"
    MEDICAL = "medical"
    OTHER = "other"


class DonationStatus(str, Enum):
    PENDING = "pending"
    AVAILABLE = "available"
    RESERVED = "reserved"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class DeliveryStatus(str, Enum):
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
