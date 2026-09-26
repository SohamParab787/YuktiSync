from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Medication(BaseModel):
    id: str
    user_id: str
    prescription_id: Optional[str] = None
    name: str
    dosage: str
    frequency: str
    times_per_day: int = 1
    scheduled_times: List[str] = Field(default_factory=list) # e.g. ["08:00", "20:00"]
    duration_days: int = 7
    start_date: str # ISO date string YYYY-MM-DD
    end_date: str # ISO date string YYYY-MM-DD
    food_instruction: Optional[str] = None # e.g. "After breakfast", "After lunch", "After dinner"
    instructions: Optional[str] = None
    active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
