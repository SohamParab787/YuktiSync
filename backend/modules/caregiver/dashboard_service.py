import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status

from backend.shared.database import db
from backend.modules.caregiver.schemas import (
    DashboardResponse,
    AdherenceStats,
    DoseItem,
    AlertItem,
    NoteResponse,
    CaregiverPermissionEnum,
)
from backend.modules.caregiver.invite_service import get_caregiver_permissions

# Integrations with Person 2 (Schedule Module)
from backend.modules.schedule.adherence_service import get_adherence_summary
from backend.modules.schedule.escalation_service import get_patient_escalations
from backend.modules.schedule.generator_service import get_upcoming_doses

logger = logging.getLogger(__name__)


async def get_dashboard(patient_id: str, requester_id: str) -> DashboardResponse:
    """
    Consolidates real-time patient adherence data, missed-dose escalation alerts,
    upcoming medication schedule, and shared patient-caregiver notes into a single
    unified payload for the Caregiver Coordination Dashboard.
    """
    # 1. Check access permissions
    perms = await get_caregiver_permissions(patient_id=patient_id, caregiver_id=requester_id)
    
    # 2. Retrieve patient profile
    patient_user = db.users.get(patient_id, {})
    patient_name = patient_user.get("name", f"Patient {patient_id}")

    # 3. Pull real-time adherence stats from Person 2's adherence_service
    try:
        adherence_raw = await get_adherence_summary(patient_id=patient_id)
    except Exception as e:
        logger.error(f"Error fetching adherence from schedule module: {e}")
        adherence_raw = {
            "adherence_rate": 0.0,
            "total_scheduled": 0,
            "taken_count": 0,
            "missed_count": 0,
            "upcoming_count": 0,
            "recent_doses": [],
        }

    adherence_stats = AdherenceStats(
        adherence_rate=adherence_raw.get("adherence_rate", 0.0),
        total_scheduled=adherence_raw.get("total_scheduled", 0),
        taken_count=adherence_raw.get("taken_count", 0),
        missed_count=adherence_raw.get("missed_count", 0),
        upcoming_count=adherence_raw.get("upcoming_count", 0),
    )

    recent_doses = [
        DoseItem(
            id=str(d.get("id", f"dose-{idx}")),
            patient_id=patient_id,
            medication_name=d.get("medication_name", "Medication"),
            dosage=d.get("dosage", "1 dose"),
            scheduled_time=d.get("scheduled_time", ""),
            taken_time=d.get("taken_time"),
            status=d.get("status", "unknown"),
            notes=d.get("notes"),
        )
        for idx, d in enumerate(adherence_raw.get("recent_doses", []))
    ]

    # 4. Pull upcoming doses from Person 2's generator_service
    try:
        upcoming_raw = await get_upcoming_doses(patient_id=patient_id)
    except Exception as e:
        logger.error(f"Error fetching upcoming doses: {e}")
        upcoming_raw = []

    upcoming_doses = [
        DoseItem(
            id=str(d.get("id", f"up-{idx}")),
            patient_id=patient_id,
            medication_name=d.get("medication_name", "Medication"),
            dosage=d.get("dosage", "1 dose"),
            scheduled_time=d.get("scheduled_time", ""),
            taken_time=None,
            status=d.get("status", "upcoming"),
            notes=d.get("notes"),
        )
        for idx, dose in enumerate(upcoming_raw)
        for d in [dose.model_dump() if hasattr(dose, "model_dump") else dose]
    ]

    # 5. Pull active missed-dose alerts & escalations from Person 2's escalation_service
    alerts = await get_alerts(patient_id=patient_id)

    # 6. Pull shared notes
    notes = await get_notes(patient_id=patient_id)

    # 7. Pull active medications on record
    medications = db.medications.get(patient_id, [])

    # 8. Pull clinical prescriptions on record
    prescriptions = db.prescriptions.get(patient_id, [])

    return DashboardResponse(
        patient_id=patient_id,
        patient_name=patient_name,
        caregiver_permission=perms.permissions,
        adherence_summary=adherence_stats,
        recent_doses=recent_doses,
        upcoming_doses=upcoming_doses,
        alerts=alerts,
        notes=notes,
        active_medications=medications,
        prescriptions=prescriptions,
    )


async def load_patient_prescription(patient_id: str, prescription_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies a new doctor's prescription to the patient's record,
    dynamically deriving active medications, dosage timetables, and alerts.
    """
    if not prescription_data.get("id"):
        prescription_data["id"] = f"rx-{uuid.uuid4().hex[:6]}"
    if not prescription_data.get("issued_date"):
        prescription_data["issued_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    db.apply_prescription(patient_id, prescription_data)
    logger.info(f"Prescription {prescription_data['id']} applied to patient {patient_id}")
    return prescription_data


async def get_alerts(patient_id: str) -> List[AlertItem]:
    """
    Surfaces missed-dose alerts from Person 2's escalation_service
    and forwards them to caregiver as notification items.
    """
    try:
        escalations = await get_patient_escalations(patient_id=patient_id)
    except Exception as e:
        logger.error(f"Error fetching escalations from Person 2 module: {e}")
        escalations = []

    alert_items = []
    for esc in escalations:
        alert_items.append(
            AlertItem(
                id=str(esc.get("id", uuid.uuid4().hex[:8])),
                patient_id=patient_id,
                medication_name=esc.get("medication_name", "Prescription"),
                alert_type=esc.get("alert_type", "missed_dose"),
                severity=esc.get("severity", "medium"),
                message=esc.get("message", "Medication dose schedule alert"),
                scheduled_time=esc.get("scheduled_time"),
                is_resolved=esc.get("is_resolved", False),
                created_at=esc.get("created_at") or datetime.now(timezone.utc),
            )
        )
    return alert_items


async def get_notes(patient_id: str) -> List[NoteResponse]:
    """
    Retrieve all shared notes between caregiver and patient.
    """
    notes = [
        NoteResponse(
            id=n["id"],
            patient_id=n["patient_id"],
            author_id=n["author_id"],
            author_name=n["author_name"],
            author_role=n["author_role"],
            content=n["content"],
            created_at=n["created_at"],
        )
        for n in db.caregiver_notes
        if n.get("patient_id") == patient_id
    ]
    # Sort latest first
    notes.sort(key=lambda x: x.created_at, reverse=True)
    return notes


async def create_note(
    patient_id: str,
    content: str,
    author: Dict[str, Any],
) -> NoteResponse:
    """
    Create a shared note. Enforces role-based permissions:
    If caregiver has 'read_only' permission, editing/note creation is disallowed.
    """
    author_id = author.get("id", "caregiver-201")
    author_role = author.get("role", "caregiver")
    author_name = author.get("name", "Caregiver")

    # Enforce permission checks
    if author_role == "caregiver":
        perms = await get_caregiver_permissions(patient_id=patient_id, caregiver_id=author_id)
        if not perms.can_add_notes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Caregiver has 'read_only' permissions and cannot post notes. Upgrade to 'read_respond' required.",
            )

    note_id = f"note-{uuid.uuid4().hex[:8]}"
    new_note = {
        "id": note_id,
        "patient_id": patient_id,
        "author_id": author_id,
        "author_name": author_name,
        "author_role": author_role,
        "content": content,
        "created_at": datetime.now(timezone.utc),
    }

    db.caregiver_notes.append(new_note)
    logger.info(f"Note {note_id} created on patient {patient_id} by {author_name} ({author_role})")

    return NoteResponse(**new_note)
