import pytest
from datetime import datetime, date, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from backend.shared.database import get_db
from backend.shared.models.dose_log import DoseLog
from backend.shared.models.medication import Medication
from backend.modules.schedule.generator_service import GeneratorService
from backend.modules.schedule.adherence_service import AdherenceService
from backend.modules.schedule.reminder_service import ReminderService
from backend.modules.schedule.escalation_service import EscalationService
from backend.modules.schedule.routes import router as schedule_router

# Setup test FastAPI app
app = FastAPI(title="MediAdhere Test App")
app.include_router(schedule_router, prefix="/api/schedule")

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_database():
    """Clear in-memory DB before each test."""
    db = get_db()
    db.clear()
    yield
    db.clear()

# =====================================================================
# 1. GeneratorService Tests
# =====================================================================
def test_parse_scheduled_times():
    assert GeneratorService.parse_scheduled_times("once daily") == ["09:00"]
    assert GeneratorService.parse_scheduled_times("twice daily") == ["08:00", "20:00"]
    assert GeneratorService.parse_scheduled_times("3 times daily") == ["08:00", "14:00", "20:00"]
    assert GeneratorService.parse_scheduled_times("custom", ["10:00", "18:00"]) == ["10:00", "18:00"]

@pytest.mark.asyncio
async def test_generate_schedule_direct_payload():
    generator = GeneratorService()
    rx_payload = {
        "medications": [
            {
                "name": "Metformin",
                "dosage": "500mg",
                "frequency": "twice daily",
                "duration_days": 3,
                "instructions": "Take with meal"
            }
        ]
    }
    result = await generator.generate_schedule(
        user_id="user-100",
        prescription_data=rx_payload,
        start_date_str="2026-10-01"
    )
    assert result["medications_created"] == 1
    # 3 days * 2 doses/day = 6 doses
    assert result["doses_created"] == 6

    db = get_db()
    user_doses = db.get_dose_logs_by_user("user-100")
    assert len(user_doses) == 6
    assert user_doses[0].medication_name == "Metformin"
    assert user_doses[0].status == "upcoming"

# =====================================================================
# 2. AdherenceService Tests
# =====================================================================
def test_log_dose_status_taken():
    db = get_db()
    dose = DoseLog(
        id="dose-1",
        medication_id="med-1",
        medication_name="Aspirin",
        dosage="81mg",
        user_id="user-1",
        scheduled_time=datetime.now().isoformat(),
        status="upcoming"
    )
    db.save_dose_log(dose)

    adherence = AdherenceService()
    updated = adherence.log_dose_status("dose-1", "taken", notes="Taken on time")
    assert updated.status == "taken"
    assert updated.notes == "Taken on time"
    assert updated.taken_at is not None

def test_auto_transition_missed_doses():
    db = get_db()
    past_time = (datetime.now() - timedelta(hours=3)).isoformat()
    dose_overdue = DoseLog(
        id="dose-overdue",
        medication_id="med-1",
        medication_name="Aspirin",
        dosage="81mg",
        user_id="user-1",
        scheduled_time=past_time,
        status="upcoming",
        grace_period_minutes=60
    )
    db.save_dose_log(dose_overdue)

    adherence = AdherenceService()
    transitioned = adherence.auto_transition_missed_doses(user_id="user-1")
    assert len(transitioned) == 1
    assert transitioned[0].id == "dose-overdue"
    assert transitioned[0].status == "missed"

def test_daily_adherence_calculation():
    db = get_db()
    today_str = date.today().isoformat()
    # 2 taken, 1 missed, 1 delayed = 4 due doses. Adherence: (2 + 0.5)/4 = 62.5%
    doses = [
        DoseLog(id="d1", medication_id="m1", medication_name="MedA", dosage="10mg", user_id="u1", scheduled_time=f"{today_str}T08:00:00", status="taken"),
        DoseLog(id="d2", medication_id="m1", medication_name="MedA", dosage="10mg", user_id="u1", scheduled_time=f"{today_str}T12:00:00", status="taken"),
        DoseLog(id="d3", medication_id="m1", medication_name="MedA", dosage="10mg", user_id="u1", scheduled_time=f"{today_str}T16:00:00", status="missed"),
        DoseLog(id="d4", medication_id="m1", medication_name="MedA", dosage="10mg", user_id="u1", scheduled_time=f"{today_str}T20:00:00", status="delayed"),
    ]
    for d in doses:
        db.save_dose_log(d)

    adherence = AdherenceService()
    summary = adherence.get_daily_adherence("u1", today_str)
    assert summary["total_doses"] == 4
    assert summary["taken_doses"] == 2
    assert summary["missed_doses"] == 1
    assert summary["delayed_doses"] == 1
    assert summary["adherence_percentage"] == 62.5

# =====================================================================
# 3. Reminder & Escalation Tests
# =====================================================================
def test_reminder_service():
    db = get_db()
    upcoming_time = (datetime.now() + timedelta(minutes=15)).isoformat()
    dose = DoseLog(
        id="d-rem",
        medication_id="m1",
        medication_name="Ibuprofen",
        dosage="200mg",
        user_id="u2",
        scheduled_time=upcoming_time,
        status="upcoming"
    )
    db.save_dose_log(dose)

    reminder_svc = ReminderService()
    reminders = reminder_svc.get_upcoming_reminders("u2", lookahead_minutes=30)
    assert len(reminders) == 1
    assert reminders[0]["medication_name"] == "Ibuprofen"

@pytest.mark.asyncio
async def test_escalation_service_ladder():
    db = get_db()
    now_past = (datetime.now() - timedelta(hours=1)).isoformat()
    # 2 consecutive missed doses
    d1 = DoseLog(id="m1", medication_id="med", medication_name="Stat1", dosage="5mg", user_id="u-esc", scheduled_time=now_past, status="missed")
    d2 = DoseLog(id="m2", medication_id="med", medication_name="Stat1", dosage="5mg", user_id="u-esc", scheduled_time=now_past, status="missed")
    db.save_dose_log(d1)
    db.save_dose_log(d2)

    escalation_svc = EscalationService()
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        res = await escalation_svc.check_and_escalate("u-esc")
        assert res["consecutive_missed"] == 2
        assert res["escalated"] is True
        assert res["alert_level"] == "WARNING"
        assert mock_post.called

# =====================================================================
# 4. Route API Tests
# =====================================================================
def test_generate_endpoint():
    response = client.post("/api/schedule/generate", json={
        "user_id": "test-user-api",
        "start_date": "2026-10-10",
        "duration_days": 2,
        "prescription_data": {
            "medications": [
                {"name": "Vitamin C", "dosage": "500mg", "frequency": "once daily"}
            ]
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["medications_created"] == 1
    assert data["doses_created"] == 2

def test_dashboard_endpoint():
    response = client.get("/api/schedule/dashboard?user_id=test-dash-user")
    assert response.status_code == 200
    data = response.json()
    assert "todays_doses" in data
    assert "adherence_summary" in data
    assert "risk_alerts" in data

def test_mark_dose_endpoint():
    db = get_db()
    dose = DoseLog(
        id="d-mark-1",
        medication_id="m1",
        medication_name="Aspirin",
        dosage="81mg",
        user_id="u-mark",
        scheduled_time=datetime.now().isoformat(),
        status="upcoming"
    )
    db.save_dose_log(dose)

    response = client.post("/api/schedule/dose/d-mark-1/mark", json={
        "status": "taken",
        "notes": "Taken with water"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["dose"]["status"] == "taken"
