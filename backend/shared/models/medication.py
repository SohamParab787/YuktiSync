from datetime import datetime, timezone
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class Medication(BaseModel):
    id: str = Field(..., description="Unique medication identifier")
    patient_id: Optional[str] = Field(default=None, description="Patient this medication is prescribed to")
    user_id: Optional[str] = Field(default=None, description="Owning patient/user ID")
    prescription_id: Optional[str] = None
    name: str = Field(..., description="Brand or generic name of medication")
    dosage: str = Field(..., description="Prescribed dosage")
    frequency: str = Field(..., description="Prescribed frequency")
    times_per_day: int = 1
    scheduled_times: List[str] = Field(default_factory=list)
    duration_days: int = 7
    start_date: Optional[Union[str, datetime]] = None
    end_date: Optional[Union[str, datetime]] = None
    food_instruction: Optional[str] = None
    instructions: Optional[str] = None
    prescribed_by: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    active: bool = True
    created_at: Union[str, datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
