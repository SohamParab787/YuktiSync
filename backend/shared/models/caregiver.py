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
    caregiver_id: Optional[str] = Field(default=None, description="ID of the caregiver account once accepted")
    caregiver_email: str = Field(..., description="Email address the invite was sent to")
    caregiver_name: Optional[str] = Field(default=None, description="Caregiver display name")
    patient_name: Optional[str] = Field(default=None, description="Patient display name")
    permissions: CaregiverPermission = Field(
        default=CaregiverPermission.READ_ONLY, 
        description="Caregiver access level: read_only or read_respond"
    )
    status: InviteStatus = Field(default=InviteStatus.PENDING, description="Status of the invitation")
    invite_token: Optional[str] = Field(default=None, description="Secure time-limited invite token")
    invite_expires_at: Optional[datetime] = Field(default=None, description="Token expiration timestamp")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaregiverNote(BaseModel):
    id: str = Field(..., description="Unique note identifier")
    patient_id: str = Field(..., description="Patient ID this note pertains to")
    author_id: str = Field(..., description="User ID of the note author")
    author_name: str = Field(..., description="Display name of the author")
    author_role: str = Field(..., description="Role of the author: caregiver or patient")
    content: str = Field(..., description="Content of the shared note")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaregiverAlert(BaseModel):
    id: str = Field(..., description="Unique alert identifier")
    patient_id: str = Field(..., description="Target patient ID")
    medication_name: str = Field(..., description="Medication name if relevant")
    alert_type: str = Field(default="missed_dose", description="Alert category: missed_dose, escalation, etc.")
    severity: str = Field(default="medium", description="Severity: low, medium, high, critical")
    message: str = Field(..., description="User-friendly alert message")
    scheduled_time: Optional[datetime] = Field(default=None, description="When dose was missed")
    is_resolved: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
