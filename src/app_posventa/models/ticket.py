from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
from pydantic import BaseModel, Field
from .enums import ModuleEnum, TicketStatus, Priority

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ActivityType(str, Enum):
    NOTE = "note"
    CALL = "call"
    EMAIL = "email"
    STATUS_CHANGE = "status_change"
    CATEGORIZATION = "categorization"
    WHATSAPP = "whatsapp"

class TicketActivity(BaseModel):
    id: str = Field(default_factory=lambda: f"ACT-{uuid.uuid4().hex[:6].upper()}")
    activity_type: ActivityType
    author: str
    author_name: Optional[str] = None
    content: str
    created_at: datetime = Field(default_factory=utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TicketNote(BaseModel):
    author: str
    content: str
    created_at: datetime = Field(default_factory=utc_now)

class TicketBase(BaseModel):
    module: ModuleEnum
    title: str
    description: str
    customer_name: Optional[str] = None
    customer_surname: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    contract_reference: Optional[str] = None
    cups: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    priority: Priority = Priority.MEDIA
    resolution: Optional[str] = None
    classification: Optional[str] = None
    recovery_channel: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[Priority] = None
    assigned_to: Optional[str] = None
    customer_name: Optional[str] = None
    customer_surname: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    contract_reference: Optional[str] = None
    cups: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    resolution: Optional[str] = None
    classification: Optional[str] = None
    recovery_channel: Optional[str] = None
    resolution_notes: Optional[str] = None

class Ticket(TicketBase):
    id: str
    status: TicketStatus = TicketStatus.ABIERTO
    assigned_to: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    notes: List[TicketNote] = Field(default_factory=list)
    activities: List[TicketActivity] = Field(default_factory=list)

    @property
    def full_customer_name(self) -> str:
        if self.customer_name and self.customer_surname:
            return f"{self.customer_name} {self.customer_surname}"
        return self.customer_name or self.customer_surname or "No indicado"
