from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


class Medication(BaseModel):
    id: str = Field(..., description="Unique medication identifier")
    patient_id: str = Field(..., description="ID of patient this medication is prescribed to")
    name: str = Field(..., description="Brand or generic name of medication")
    dosage: str = Field(..., description="Dosage string (e.g. 500mg, 1 tablet)")
    frequency: str = Field(..., description="Frequency string (e.g. Twice daily, Once every morning)")
    instructions: Optional[str] = Field(default=None, description="Special instructions e.g. With food")
    prescribed_by: Optional[str] = Field(default=None, description="Doctor/Prescriber name")
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    warnings: List[str] = Field(default_factory=list, description="Known drug warnings or tags")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
