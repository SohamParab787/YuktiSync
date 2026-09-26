import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.shared.database import db
from backend.modules.caregiver.schemas import CaregiverPermissionEnum

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db_state():
    """Ensure database has clean demo state before each test"""
    db.__init__(seed_demo=True)


# ====================================================
# 1. INVITATION & ACCESS CONTROL TESTS
# ====================================================

def test_create_invite_success():
    """Test generating a secure caregiver invitation"""
    payload = {
        "patient_id": "patient-101",
        "caregiver_email": "newcaregiver@example.com",
        "caregiver_name": "Anita Patel",
        "permissions": "read_respond",
        "expires_in_days": 5,
    }
    response = client.post(
        "/api/caregiver/invite",
        json=payload,
        headers={"X-User-Id": "patient-101", "X-User-Role": "patient"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == "patient-101"
    assert data["caregiver_email"] == "newcaregiver@example.com"
    assert data["permissions"] == "read_respond"
    assert data["status"] == "pending"
    assert data["invite_token"] is not None
    assert "/caregiver/invite?token=" in data["invite_url"]


def test_accept_invite_success():
    """Test accepting an invite token establishes relationship"""
    # 1. Create invite
    create_resp = client.post(
        "/api/caregiver/invite",
        json={
            "patient_id": "patient-101",
            "caregiver_email": "son@example.com",
            "permissions": "read_respond",
            "expires_in_days": 3,
        },
    )
    assert create_resp.status_code == 201
    invite_token = create_resp.json()["invite_token"]

    # 2. Accept invite
    accept_resp = client.post(
        "/api/caregiver/invite/accept",
        json={
            "invite_token": invite_token,
            "caregiver_id": "caregiver-son-99",
            "caregiver_name": "Amit Patel",
        },
        headers={"X-User-Id": "caregiver-son-99", "X-User-Role": "caregiver"},
    )
    assert accept_resp.status_code == 200
    acc_data = accept_resp.json()
    assert acc_data["status"] == "accepted"
    assert acc_data["caregiver_id"] == "caregiver-son-99"
    assert acc_data["caregiver_name"] == "Amit Patel"
    assert acc_data["permissions"] == "read_respond"


def test_accept_invalid_or_expired_token():
    """Test accepting invalid token fails with 400 Bad Request"""
    response = client.post(
        "/api/caregiver/invite/accept",
        json={"invite_token": "invalid-bogus-token-xyz"},
    )
    assert response.status_code == 400
    assert "Invalid" in response.json()["detail"]


def test_revoke_caregiver_access():
    """Test revoking access terminates permission"""
    # Use existing demo link
    link_id = "link-001"
    assert link_id in db.caregiver_links

    resp = client.delete(
        f"/api/caregiver/invite/{link_id}",
        headers={"X-User-Id": "patient-101", "X-User-Role": "patient"},
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert db.caregiver_links[link_id]["status"] == "revoked"


# ====================================================
# 2. DASHBOARD PAYLOAD SHAPE & PERMISSION TESTS
# ====================================================

def test_get_dashboard_payload_shape():
    """Verify consolidated dashboard response contains all required fields"""
    response = client.get(
        "/api/caregiver/dashboard/patient-101",
        headers={"X-User-Id": "caregiver-201", "X-User-Role": "caregiver"},
    )
    assert response.status_code == 200
    data = response.json()

    # Verify root fields
    assert data["patient_id"] == "patient-101"
    assert "patient_name" in data
    assert data["caregiver_permission"] in ["read_only", "read_respond"]

    # Verify adherence_summary shape
    summary = data["adherence_summary"]
    assert "adherence_rate" in summary
    assert "total_scheduled" in summary
    assert "taken_count" in summary
    assert "missed_count" in summary
    assert "upcoming_count" in summary
    assert isinstance(summary["adherence_rate"], float)

    # Verify dose arrays
    assert isinstance(data["recent_doses"], list)
    assert len(data["recent_doses"]) > 0
    dose0 = data["recent_doses"][0]
    assert "medication_name" in dose0
    assert "dosage" in dose0
    assert "status" in dose0

    # Verify upcoming doses
    assert isinstance(data["upcoming_doses"], list)
    
    # Verify alerts feed
    assert isinstance(data["alerts"], list)
    assert len(data["alerts"]) > 0
    alert0 = data["alerts"][0]
    assert "medication_name" in alert0
    assert "severity" in alert0
    assert "message" in alert0

    # Verify shared notes
    assert isinstance(data["notes"], list)
    assert len(data["notes"]) > 0
    note0 = data["notes"][0]
    assert "author_name" in note0
    assert "content" in note0


def test_caregiver_notes_permission_enforcement():
    """Verify read_only caregiver cannot create notes while read_respond can"""
    # 1. Modify demo link to read_only
    db.caregiver_links["link-001"]["permissions"] = CaregiverPermissionEnum.READ_ONLY.value

    # Attempt to post note as read_only caregiver
    fail_resp = client.post(
        "/api/caregiver/notes",
        json={
            "patient_id": "patient-101",
            "content": "Trying to post note without write permissions",
        },
        headers={"X-User-Id": "caregiver-201", "X-User-Role": "caregiver"},
    )
    assert fail_resp.status_code == 403
    assert "read_only" in fail_resp.json()["detail"]

    # 2. Upgrade demo link to read_respond
    db.caregiver_links["link-001"]["permissions"] = CaregiverPermissionEnum.READ_RESPOND.value

    success_resp = client.post(
        "/api/caregiver/notes",
        json={
            "patient_id": "patient-101",
            "content": "Patient reported feeling well after morning medication.",
        },
        headers={"X-User-Id": "caregiver-201", "X-User-Role": "caregiver", "X-User-Name": "Priya Patel"},
    )
    assert success_resp.status_code == 201
    created_note = success_resp.json()
    assert created_note["content"] == "Patient reported feeling well after morning medication."
    assert created_note["author_name"] == "Priya Patel"


def test_get_alerts_feed():
    """Test retrieving alerts feed for patient"""
    response = client.get("/api/caregiver/alerts/patient-101")
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) >= 1
    assert any("Lisinopril" in a["medication_name"] for a in alerts)


# ====================================================
# 3. RAG-GROUNDED CHAT ASSISTANT TESTS
# ====================================================

def test_chat_assistant_schedule_query():
    """Test asking 'What do I take now?' returns grounded schedule details and sources"""
    response = client.post(
        "/api/caregiver/chat",
        json={
            "patient_id": "patient-101",
            "query": "What do I take now?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "What do I take now?"
    assert len(data["sources"]) > 0
    # Must contain schedule_service source
    source_modules = [s["module"] for s in data["sources"]]
    assert "schedule_service" in source_modules
    # Must contain informative answer
    assert "Metformin" in data["answer"] or "schedule" in data["answer"].lower()
    assert "Disclaimer" in data["answer"]


def test_chat_assistant_interaction_risk_check_with_mocks():
    """
    Test scenario with mocked risk and explainer responses:
    Verify risk check is triggered when query mentions drug combination (e.g. Ibuprofen),
    structured sources include risk analysis, and high-severity flag is set.
    """
    mock_interactions = [
        {
            "drugs": ["Lisinopril", "Ibuprofen"],
            "type": "drug-drug",
            "severity": "high",
            "summary": "NSAIDs reduce Lisinopril efficacy and may impair renal function.",
            "recommendation": "Avoid concurrent use without physician guidance.",
        }
    ]

    with patch(
        "backend.modules.caregiver.chat_assistant_service.check_drug_interactions",
        new=AsyncMock(return_value=mock_interactions),
    ), patch(
        "backend.modules.caregiver.chat_assistant_service.classify_severity",
        return_value="high",
    ):
        response = client.post(
            "/api/caregiver/chat",
            json={
                "patient_id": "patient-101",
                "query": "Can I take Ibuprofen with my morning medicines?",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["severity"] == "high"
        assert data["requires_escalation"] is True
        
        # Verify sources include risk_interaction module
        risk_source = next((s for s in data["sources"] if s["module"] == "risk_interaction"), None)
        assert risk_source is not None
        assert "Lisinopril" in risk_source["snippet"]
        assert "Ibuprofen" in risk_source["snippet"]


def test_chat_assistant_graceful_fallback_on_service_failure():
    """Test that when a dependent service raises an exception, the assistant degrades gracefully"""
    with patch(
        "backend.modules.caregiver.chat_assistant_service.get_adherence_summary",
        side_effect=Exception("Database timeout"),
    ):
        response = client.post(
            "/api/caregiver/chat",
            json={
                "patient_id": "patient-101",
                "query": "Is my blood pressure pill safe?",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] is not None
        assert "Disclaimer" in data["answer"]
