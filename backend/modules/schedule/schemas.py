from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class DoseStatusEnum(str, Enum):
    PENDING = "pending"
    UPCOMING = "upcoming"
    TAKEN = "taken"
    MISSED = "missed"
    DELAYED = "delayed"
    SKIPPED = "skipped"

class ScheduleGenerateRequest(BaseModel):
    user_id: str
    prescription_id: Optional[str] = None
    start_date: Optional[str] = None # YYYY-MM-DD
    duration_days: Optional[int] = None
    prescription_data: Optional[Dict[str, Any]] = None # Direct payload option if offline

class ScheduleGenerateResponse(BaseModel):
    message: str
    medications_created: int
    doses_created: int
    medication_ids: List[str]

class MarkDoseRequest(BaseModel):
    status: str # "taken", "missed", "delayed", "skipped", "pending"
    taken_at: Optional[str] = None
    notes: Optional[str] = None

class DoseLogSchema(BaseModel):
    id: str
    medication_id: str
    medication_name: str
    dosage: str
    user_id: str
    scheduled_time: str
    status: str # "pending", "upcoming", "taken", "delayed", "missed", "skipped"
    food_instruction: Optional[str] = None # e.g. "After breakfast", "After lunch", "After dinner"
    taken_at: Optional[str] = None
    notes: Optional[str] = None
    instructions: Optional[str] = None
    grace_period_minutes: int = 60
    created_at: str

class MarkDoseResponse(BaseModel):
    success: bool
    dose: DoseLogSchema
    message: str

class AdherenceSummaryResponse(BaseModel):
    user_id: str
    date: str
    period: str # "today", "week", "month"
    total_doses: int
    taken_doses: int
    missed_doses: int
    delayed_doses: int
    upcoming_doses: int
    adherence_percentage: float

class NextDoseInfo(BaseModel):
    dose_id: str
    medication_id: str
    medication_name: str
    dosage: str
    scheduled_time: str
    seconds_remaining: int
    food_instruction: Optional[str] = None
    instructions: Optional[str] = None

class MissedDoseAlert(BaseModel):
    dose_id: str
    medication_name: str
    dosage: str
    scheduled_time: str
    message: str

class RiskAlertSchema(BaseModel):
    id: Optional[str] = "risk-1"
    type: Optional[str] = "drug_interaction"
    severity: str # "CRITICAL", "WARNING", "INFO"
    title: str
    explanation: str
    medications: List[str] = Field(default_factory=list)

class EscalationStatus(BaseModel):
    consecutive_missed: int
    alert_level: str # "NONE", "INFO", "WARNING", "CRITICAL"
    escalated_to_caregiver: bool
    message: str

class AntiStackingCheckRequest(BaseModel):
    user_id: str
    medication_name: str
    dose_id: Optional[str] = None

class AntiStackingCheckResponse(BaseModel):
    status: str # "SAFE TO TAKE", "WAIT / SKIP", "CONSULT PROFESSIONAL"
    recommendation: str
    hours_until_next_dose: Optional[float] = None
    next_scheduled_time: Optional[str] = None
    stacking_risk_detected: bool = False
    disclaimer: str = "Medication decisions should follow prescribed instructions or professional guidance. Never automatically change your prescribed dosage."

class ActivityLogSchema(BaseModel):
    id: str
    user_id: str
    dose_id: str
    medication_name: str
    action: str
    details: Optional[str] = None
    timestamp: str

class EscalationRecordSchema(BaseModel):
    id: str
    user_id: str
    alert_level: str
    consecutive_missed: int
    medications: List[str]
    timestamp: str
    message: str

class DailyBreakdownItem(BaseModel):
    date: str
    total_doses: int
    taken_doses: int
    missed_doses: int
    delayed_doses: int
    upcoming_doses: int
    adherence_percentage: float
    doses: List[DoseLogSchema]

class DashboardResponse(BaseModel):
    user_id: str
    date: str
    greeting: str = "Good Morning"
    todays_doses: List[DoseLogSchema]
    next_dose: Optional[NextDoseInfo] = None
    adherence_summary: AdherenceSummaryResponse
    missed_alerts: List[MissedDoseAlert] = Field(default_factory=list)
    risk_alerts: List[RiskAlertSchema] = Field(default_factory=list)
    escalation_status: Optional[EscalationStatus] = None
    anti_stacking_advice: Optional[AntiStackingCheckResponse] = None
    recent_activities: List[ActivityLogSchema] = Field(default_factory=list)

class ScheduleTimelineResponse(BaseModel):
    user_id: str
    view_type: str # "daily" or "weekly"
    start_date: str
    end_date: str
    doses: List[DoseLogSchema]
    daily_breakdown: List[DailyBreakdownItem] = Field(default_factory=list)

class EscalationRequest(BaseModel):
    user_id: str
    caregiver_api_url: Optional[str] = None

class EscalationResponse(BaseModel):
    user_id: str
    consecutive_missed: int
    escalated: bool
    alert_level: str
    message: str
