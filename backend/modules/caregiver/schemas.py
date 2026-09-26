from datetime import datetime
from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, EmailStr


class CaregiverPermissionEnum(str, Enum):
    READ_ONLY = "read_only"
    READ_RESPOND = "read_respond"


class InviteStatusEnum(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class InviteCreateRequest(BaseModel):
    patient_id: str = Field(..., description="ID of the patient inviting a caregiver")
    caregiver_email: EmailStr = Field(..., description="Email address of the caregiver")
    caregiver_name: Optional[str] = Field(default=None, description="Optional name of the caregiver")
    permissions: CaregiverPermissionEnum = Field(
        default=CaregiverPermissionEnum.READ_ONLY,
        description="Permission level: read_only or read_respond"
    )
    expires_in_days: int = Field(default=7, ge=1, le=30, description="Invite token validity duration in days")


class InviteAcceptRequest(BaseModel):
    invite_token: str = Field(..., description="Secure signed invitation token")
    caregiver_id: Optional[str] = Field(default=None, description="Caregiver user ID if known/logged in")
    caregiver_name: Optional[str] = Field(default=None, description="Display name for caregiver profile")


class CaregiverPermissions(BaseModel):
    patient_id: str
    caregiver_id: str
    permissions: CaregiverPermissionEnum
    can_view_adherence: bool = True
    can_view_schedule: bool = True
    can_add_notes: bool = False
    can_manage_alerts: bool = False


class CaregiverPatientLinkResponse(BaseModel):
    id: str
    patient_id: str
    caregiver_id: Optional[str] = None
    caregiver_email: str
    caregiver_name: Optional[str] = None
    patient_name: Optional[str] = None
    permissions: CaregiverPermissionEnum
    status: InviteStatusEnum
    invite_token: Optional[str] = None
    invite_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class NoteCreateRequest(BaseModel):
    patient_id: str = Field(..., description="ID of patient this note is for")
    content: str = Field(..., min_length=1, max_length=2000, description="Text body of the note")


class NoteResponse(BaseModel):
    id: str
    patient_id: str
    author_id: str
    author_name: str
    author_role: str
    content: str
    created_at: datetime


class AlertItem(BaseModel):
    id: str
    patient_id: str
    medication_name: str
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    scheduled_time: Optional[Any] = None
    is_resolved: bool = False
    created_at: datetime


class DoseItem(BaseModel):
    id: str
    patient_id: str
    medication_name: str
    dosage: str
    scheduled_time: Any
    taken_time: Optional[Any] = None
    status: str
    notes: Optional[str] = None


class AdherenceStats(BaseModel):
    adherence_rate: float
    total_scheduled: int
    taken_count: int
    missed_count: int
    upcoming_count: int


class DashboardResponse(BaseModel):
    patient_id: str
    patient_name: str
    caregiver_permission: CaregiverPermissionEnum
    adherence_summary: AdherenceStats
    recent_doses: List[DoseItem] = Field(default_factory=list)
    upcoming_doses: List[DoseItem] = Field(default_factory=list)
    alerts: List[AlertItem] = Field(default_factory=list)
    notes: List[NoteResponse] = Field(default_factory=list)
    active_medications: List[Dict[str, Any]] = Field(default_factory=list)
    prescriptions: List[Dict[str, Any]] = Field(default_factory=list)


class PrescriptionUploadRequest(BaseModel):
    patient_id: str = Field(..., description="Target patient ID")
    doctor_name: str = Field(..., description="Prescribing physician name")
    clinic_name: Optional[str] = Field(default="Healthcare Clinic", description="Clinic/Hospital name")
    rx_number: Optional[str] = Field(default=None, description="Prescription/Rx registration number")
    diagnosis: Optional[str] = Field(default=None, description="Clinical diagnosis or therapeutic indication")
    instructions: Optional[str] = Field(default=None, description="General prescription advice")
    medications: List[Dict[str, Any]] = Field(..., description="List of prescribed medications")


class ChatQueryRequest(BaseModel):
    patient_id: str = Field(..., description="Target patient ID")
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language question")


class SourceItem(BaseModel):
    module: str  # prescription_explainer, risk_interaction, schedule_service
    title: str
    details: Dict[str, Any] = Field(default_factory=dict)
    snippet: str


class ChatResponse(BaseModel):
    query: str
    answer: str
    patient_id: str
    sources: List[SourceItem] = Field(default_factory=list)
    severity: str = "none"  # none, low, medium, high, critical
    requires_escalation: bool = False
    timestamp: datetime
