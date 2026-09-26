from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DoseStatus(str, Enum):
    TAKEN = "taken"
    MISSED = "missed"
    UPCOMING = "upcoming"
    SKIPPED = "skipped"


class DoseLog(BaseModel):
    id: str = Field(..., description="Unique dose event ID")
    patient_id: str = Field(..., description="Patient ID")
    medication_id: Optional[str] = Field(default=None, description="Associated medication ID")
    medication_name: str = Field(..., description="Name of medication")
    dosage: str = Field(..., description="Scheduled dosage")
    scheduled_time: datetime = Field(..., description="Expected time of dose")
    taken_time: Optional[datetime] = Field(default=None, description="Actual time taken")
    status: DoseStatus = Field(default=DoseStatus.UPCOMING, description="Dose status")
    notes: Optional[str] = Field(default=None, description="Patient/Caregiver log notes")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
