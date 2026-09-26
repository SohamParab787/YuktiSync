from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DoseLog(BaseModel):
    id: str
    medication_id: str
    medication_name: str
    dosage: str
    user_id: str
    scheduled_time: str # ISO datetime YYYY-MM-DDTHH:MM:SS
    status: str = "upcoming" # "upcoming", "taken", "missed", "delayed"
    taken_at: Optional[str] = None
    notes: Optional[str] = None
    instructions: Optional[str] = None
    grace_period_minutes: int = 60
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
