"""
Pydantic schemas for the Risk module (Person 3).
These define the exact JSON shape other teammates' frontend/backend code
should send to and expect from these endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


# ---------- Feature 4: Interaction Checker ----------

class InteractionCheckRequest(BaseModel):
    medications: List[str] = Field(..., json_schema_extra={"example": ["Warfarin", "Ibuprofen"]})
    allergies: Optional[List[str]] = Field(default=[], json_schema_extra={"example": ["Penicillin"]})
    food_items: Optional[List[str]] = Field(default=[], json_schema_extra={"example": ["Grapefruit"]})


class InteractionResult(BaseModel):
    drug_a: str
    drug_b: str
    severity: SeverityLevel
    hazard: str  # short biological hazard name
    explanation: str  # plain-English explanation for the user


class AllergyWarning(BaseModel):
    medication: str
    allergen: str
    severity: SeverityLevel
    explanation: str


class FoodWarning(BaseModel):
    medication: str
    food_item: str
    severity: SeverityLevel
    explanation: str


class InteractionCheckResponse(BaseModel):
    has_critical: bool
    drug_interactions: List[InteractionResult] = []
    allergy_warnings: List[AllergyWarning] = []
    food_warnings: List[FoodWarning] = []
    summary: str


# ---------- Feature 7: Anti-Stacking / Missed-Dose Rescheduling ----------

class MissedDoseRequest(BaseModel):
    drug_name: str = Field(..., json_schema_extra={"example": "Metformin"})
    scheduled_time: datetime = Field(..., json_schema_extra={"example": "2026-09-26T08:00:00"})
    current_time: datetime = Field(..., json_schema_extra={"example": "2026-09-26T13:00:00"})
    next_scheduled_time: datetime = Field(..., json_schema_extra={"example": "2026-09-26T20:00:00"})
    dosing_interval_hours: Optional[float] = Field(
        default=None,
        description="Hours between normal doses. If omitted, calculated from scheduled_time/next_scheduled_time."
    )


class MissedDoseAction(str, Enum):
    TAKE_NOW = "TAKE_NOW"
    TAKE_NOW_DELAY_NEXT = "TAKE_NOW_DELAY_NEXT"
    SKIP_DOSE = "SKIP_DOSE"
    CONSULT_DOCTOR = "CONSULT_DOCTOR"


class MissedDoseResponse(BaseModel):
    action: MissedDoseAction
    severity: SeverityLevel
    message: str  # user-facing message
    reasoning: str  # plain-English clinical reasoning
    adjusted_next_dose_time: Optional[datetime] = None
    hours_late: float
