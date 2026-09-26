from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CaregiverPermission(str, Enum):
    READ_ONLY = "read_only"
    READ_RESPOND = "read_respond"


class InviteStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class CaregiverPatientLink(BaseModel):
    id: str = Field(..., description="Unique link identifier")
    patient_id: str = Field(..., description="ID of the patient")
    caregiver_id: Optional[str] = Field(default=None, description="Caregiver account ID once accepted")
    caregiver_email: str = Field(..., description="Email address the invite was sent to")
    caregiver_name: Optional[str] = None
    patient_name: Optional[str] = None
    permissions: CaregiverPermission = CaregiverPermission.READ_ONLY
    status: InviteStatus = InviteStatus.PENDING
    invite_token: Optional[str] = None
    invite_expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaregiverNote(BaseModel):
    id: str
    patient_id: str
    author_id: str
    author_name: str
    author_role: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaregiverAlert(BaseModel):
    id: str
    patient_id: str
    medication_name: str
    alert_type: str = "missed_dose"
    severity: str = "medium"
    message: str
    scheduled_time: Optional[datetime] = None
    is_resolved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Caregiver(BaseModel):
    id: str
    user_id: str
    name: str
    phone: Optional[str] = None
    email: str
    status: str = "active"
