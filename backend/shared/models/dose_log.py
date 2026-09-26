from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class DoseStatus(str, Enum):
    PENDING = "pending"
    UPCOMING = "upcoming"
    TAKEN = "taken"
    DELAYED = "delayed"
    MISSED = "missed"
    SKIPPED = "skipped"


class DoseLog(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: str = Field(..., description="Unique dose event ID")
    patient_id: Optional[str] = Field(default=None, description="Patient ID")
    medication_id: Optional[str] = Field(default=None, description="Associated medication ID")
    medication_name: str = Field(..., description="Name of medication")
    dosage: str = Field(..., description="Scheduled dosage")
    user_id: Optional[str] = Field(default=None, description="Owning patient/user ID")
    scheduled_time: str = Field(..., description="Expected dose time")
    taken_time: Optional[Union[str, datetime]] = Field(default=None, description="Legacy actual time taken")
    taken_at: Optional[Union[str, datetime]] = Field(default=None, description="Actual time taken")
    status: DoseStatus = Field(default=DoseStatus.PENDING, description="Dose status")
    food_instruction: Optional[str] = None
    notes: Optional[str] = Field(default=None, description="Patient/caregiver log notes")
    instructions: Optional[str] = None
    grace_period_minutes: int = 60
    created_at: Union[str, datetime] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
