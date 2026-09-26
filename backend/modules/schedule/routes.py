import httpx
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body

from backend.modules.schedule.schemas import (
    ScheduleGenerateRequest, ScheduleGenerateResponse,
    MarkDoseRequest, MarkDoseResponse,
    AdherenceSummaryResponse, DashboardResponse,
    ScheduleTimelineResponse, EscalationResponse, EscalationRequest,
    DoseLogSchema, NextDoseInfo, MissedDoseAlert, RiskAlertSchema,
    AntiStackingCheckRequest, AntiStackingCheckResponse,
    ActivityLogSchema, EscalationRecordSchema
)
from backend.modules.schedule.generator_service import GeneratorService
from backend.modules.schedule.adherence_service import AdherenceService
from backend.modules.schedule.reminder_service import ReminderService
from backend.modules.schedule.escalation_service import EscalationService
from backend.shared.database import get_db

router = APIRouter()

generator_service = GeneratorService()
adherence_service = AdherenceService()
reminder_service = ReminderService()
escalation_service = EscalationService()

def get_time_greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good Morning"
    elif hour < 17:
        return "Good Afternoon"
    else:
        return "Good Evening"

async def fetch_risk_data_from_api(user_id: str, base_url: str = "http://localhost:8000") -> List[Dict[str, Any]]:
    """
    Consumes Person 3's /api/risk/* endpoint over HTTP.
    Strict rule: Pass through severity and explanation without local re-classification.
    """
    urls_to_try = [
        f"{base_url}/api/risk/check?user_id={user_id}",
        f"{base_url}/api/risk/user/{user_id}",
        f"{base_url}/api/risk/assess?user_id={user_id}"
    ]
    for url in urls_to_try:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        return data.get("alerts", data.get("risks", []))
        except Exception:
            continue
    return []

@router.post("/generate", response_model=ScheduleGenerateResponse)
async def generate_schedule(req: ScheduleGenerateRequest):
    """
    Generate schedule timetable from prescription data for a user with food instructions.
    """
    try:
        result = await generator_service.generate_schedule(
            user_id=req.user_id,
            prescription_id=req.prescription_id,
            prescription_data=req.prescription_data,
            start_date_str=req.start_date,
            duration_days=req.duration_days
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate schedule: {str(e)}")

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    user_id: str = Query("user-1", description="Patient User ID"),
    base_url: str = Query("http://localhost:8000", description="Backend Base URL for HTTP inter-module calls")
):
    """
    Patient Dashboard Endpoint for YuktiSync:
    Returns today's doses, next scheduled dose, adherence summary, missed dose alerts,
    risk alerts, greeting, anti-stacking safety recommendation, and recent medication activities.
    """
    # 1. Auto-transition missed doses on read
    adherence_service.auto_transition_missed_doses(user_id=user_id)

    # 2. Get today's doses
    today_str = date.today().isoformat()
    all_user_doses = get_db().get_dose_logs_by_user(user_id)
    
    # If user has no doses at all, generate an initial default schedule for user
    if not all_user_doses:
        await generator_service.generate_schedule(user_id=user_id, start_date_str=today_str)
        all_user_doses = get_db().get_dose_logs_by_user(user_id)

    todays_doses = [d for d in all_user_doses if d.scheduled_time.startswith(today_str)]
    todays_doses.sort(key=lambda x: x.scheduled_time)

    # 3. Identify Next Scheduled Dose
    now = datetime.now()
    now_iso = now.isoformat()
    upcoming_doses = [d for d in todays_doses if d.status in ["pending", "upcoming"] and d.scheduled_time >= now_iso]
    
    next_dose_info = None
    if upcoming_doses:
        next_d = upcoming_doses[0]
        try:
            sched_dt = datetime.fromisoformat(next_d.scheduled_time)
            secs_remaining = max(0, int((sched_dt - now).total_seconds()))
            next_dose_info = NextDoseInfo(
                dose_id=next_d.id,
                medication_id=next_d.medication_id,
                medication_name=next_d.medication_name,
                dosage=next_d.dosage,
                scheduled_time=next_d.scheduled_time,
                seconds_remaining=secs_remaining,
                food_instruction=next_d.food_instruction,
                instructions=next_d.instructions
            )
        except ValueError:
            pass

    # 4. Adherence summary
    adherence_data = adherence_service.get_daily_adherence(user_id=user_id, target_date_str=today_str)
    adherence_summary = AdherenceSummaryResponse(**adherence_data)

    # 5. Missed Dose Alerts
    missed_doses = [d for d in todays_doses if d.status in ["missed", "skipped"]]
    missed_alerts = [
        MissedDoseAlert(
            dose_id=d.id,
            medication_name=d.medication_name,
            dosage=d.dosage,
            scheduled_time=d.scheduled_time,
            message=f"Missed scheduled dose for {d.medication_name} ({d.dosage})."
        )
        for d in missed_doses
    ]

    # 6. Fetch Risk Data via HTTP from Person 3's /api/risk/*
    raw_risk_alerts = await fetch_risk_data_from_api(user_id=user_id, base_url=base_url)
    parsed_risk_alerts = []
    for r in raw_risk_alerts:
        parsed_risk_alerts.append(
            RiskAlertSchema(
                id=str(r.get("id", "risk-alert")),
                type=str(r.get("type", "drug_interaction")),
                severity=str(r.get("severity", "WARNING")),
                title=str(r.get("title", "Drug Interaction / Stacking Alert")),
                explanation=str(r.get("explanation", r.get("message", "Interaction detected"))),
                medications=r.get("medications", [])
            )
        )

    # 7. Escalation Check Status
    esc_status_raw = await escalation_service.check_and_escalate(user_id=user_id)
    esc_status = {
        "consecutive_missed": esc_status_raw.get("consecutive_missed", 0),
        "alert_level": esc_status_raw.get("alert_level", "NONE"),
        "escalated_to_caregiver": esc_status_raw.get("escalated", False),
        "message": esc_status_raw.get("message", "")
    }

    # 8. Anti-Stacking Safety Advice
    anti_stacking_data = None
    if next_dose_info:
        anti_stacking_data = adherence_service.evaluate_anti_stacking(
            user_id=user_id,
            dose_id=next_dose_info.dose_id,
            medication_name=next_dose_info.medication_name
        )
    elif missed_doses:
        anti_stacking_data = adherence_service.evaluate_anti_stacking(
            user_id=user_id,
            dose_id=missed_doses[0].id,
            medication_name=missed_doses[0].medication_name
        )
    else:
        anti_stacking_data = adherence_service.evaluate_anti_stacking(user_id=user_id)

    # 9. Recent activities
    recent_activities = [
        ActivityLogSchema(**act) for act in get_db().get_activities(user_id, limit=5)
    ]

    return DashboardResponse(
        user_id=user_id,
        date=today_str,
        greeting=get_time_greeting(),
        todays_doses=[DoseLogSchema(**d.model_dump()) for d in todays_doses],
        next_dose=next_dose_info,
        adherence_summary=adherence_summary,
        missed_alerts=missed_alerts,
        risk_alerts=parsed_risk_alerts,
        escalation_status=esc_status,
        anti_stacking_advice=AntiStackingCheckResponse(**anti_stacking_data) if anti_stacking_data else None,
        recent_activities=recent_activities
    )

@router.get("/today", response_model=List[DoseLogSchema])
async def get_todays_doses(user_id: str = Query("user-1")):
    """
    Get today's scheduled doses for patient.
    """
    adherence_service.auto_transition_missed_doses(user_id=user_id)
    today_str = date.today().isoformat()
    all_doses = get_db().get_dose_logs_by_user(user_id)
    todays = [d for d in all_doses if d.scheduled_time.startswith(today_str)]
    todays.sort(key=lambda x: x.scheduled_time)
    return [DoseLogSchema(**d.model_dump()) for d in todays]

@router.get("/timeline", response_model=ScheduleTimelineResponse)
async def get_timeline(
    user_id: str = Query("user-1"),
    view_type: str = Query("daily", description="daily or weekly"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD")
):
    """
    Get schedule timeline view (daily or weekly).
    """
    if view_type.lower() == "weekly":
        res = adherence_service.get_weekly_adherence(user_id=user_id, start_date_str=start_date)
        all_doses_raw = get_db().get_dose_logs_by_user(user_id)
        doses_in_range = [
            d for d in all_doses_raw
            if res["start_date"] <= d.scheduled_time[:10] <= res["end_date"]
        ]
        return ScheduleTimelineResponse(
            user_id=user_id,
            view_type="weekly",
            start_date=res["start_date"],
            end_date=res["end_date"],
            doses=[DoseLogSchema(**d.model_dump()) for d in doses_in_range],
            daily_breakdown=res["daily_breakdown"]
        )
    else: # daily
        target_d = start_date or date.today().isoformat()
        adherence_service.auto_transition_missed_doses(user_id=user_id)
        all_doses = get_db().get_dose_logs_by_user(user_id)
        day_doses = [d for d in all_doses if d.scheduled_time.startswith(target_d)]
        day_doses.sort(key=lambda x: x.scheduled_time)
        return ScheduleTimelineResponse(
            user_id=user_id,
            view_type="daily",
            start_date=target_d,
            end_date=target_d,
            doses=[DoseLogSchema(**d.model_dump()) for d in day_doses],
            daily_breakdown=[]
        )

@router.get("/adherence", response_model=AdherenceSummaryResponse)
async def get_adherence(
    user_id: str = Query("user-1"),
    period: str = Query("today", description="today or week"),
    target_date: Optional[str] = Query(None)
):
    """
    Get adherence statistics.
    """
    if period == "week":
        res = adherence_service.get_weekly_adherence(user_id=user_id, start_date_str=target_date)
        return AdherenceSummaryResponse(
            user_id=user_id,
            date=res["start_date"],
            period="week",
            total_doses=res["total_doses"],
            taken_doses=res["taken_doses"],
            missed_doses=res["missed_doses"],
            delayed_doses=res["delayed_doses"],
            upcoming_doses=res["upcoming_doses"],
            adherence_percentage=res["overall_adherence_percentage"]
        )
    else:
        res = adherence_service.get_daily_adherence(user_id=user_id, target_date_str=target_date)
        return AdherenceSummaryResponse(**res)

@router.post("/dose/{dose_id}/mark", response_model=MarkDoseResponse)
async def mark_dose(dose_id: str, req: MarkDoseRequest):
    """
    Quick action endpoint to log status (taken/missed/delayed/skipped) for a dose.
    """
    try:
        updated_dose = adherence_service.log_dose_status(
            dose_id=dose_id,
            status=req.status,
            taken_at=req.taken_at,
            notes=req.notes
        )
        return MarkDoseResponse(
            success=True,
            dose=DoseLogSchema(**updated_dose.model_dump()),
            message=f"Dose status updated to '{updated_dose.status}'."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark dose: {str(e)}")

@router.post("/anti-stacking/check", response_model=AntiStackingCheckResponse)
async def check_anti_stacking(req: AntiStackingCheckRequest):
    """
    Checks if a late or missed dose is safe to take or risks dose stacking.
    """
    result = adherence_service.evaluate_anti_stacking(
        user_id=req.user_id,
        dose_id=req.dose_id,
        medication_name=req.medication_name
    )
    return AntiStackingCheckResponse(**result)

@router.post("/check-escalations", response_model=EscalationResponse)
async def check_escalations(
    req: EscalationRequest = Body(default=None),
    user_id: Optional[str] = Query(None),
    caregiver_api_url: Optional[str] = Query(None)
):
    """
    Triggers consecutive missed dose escalation check and calls Caregiver API over HTTP.
    """
    target_user_id = (req and req.user_id) or user_id or "user-1"
    target_url = (req and req.caregiver_api_url) or caregiver_api_url or "http://localhost:8000/api/caregiver/alert"
    
    res = await escalation_service.check_and_escalate(user_id=target_user_id, caregiver_api_url=target_url)
    return EscalationResponse(
        user_id=target_user_id,
        consecutive_missed=res["consecutive_missed"],
        escalated=res["escalated"],
        alert_level=res["alert_level"],
        message=res["message"]
    )

@router.get("/escalations", response_model=List[EscalationRecordSchema])
async def get_escalation_records(user_id: str = Query("user-1")):
    """
    Returns recorded escalation history for the patient.
    """
    return [EscalationRecordSchema(**e) for e in get_db().get_escalations(user_id)]

@router.get("/activities", response_model=List[ActivityLogSchema])
async def get_activity_records(user_id: str = Query("user-1"), limit: int = Query(10)):
    """
    Returns recent medication activity logs.
    """
    return [ActivityLogSchema(**a) for a in get_db().get_activities(user_id, limit=limit)]

@router.get("/reminders")
async def get_reminders(
    user_id: str = Query("user-1"),
    lookahead_minutes: int = Query(30)
):
    """
    Returns upcoming dose reminders within lookahead window.
    """
    return reminder_service.get_upcoming_reminders(user_id=user_id, lookahead_minutes=lookahead_minutes)
