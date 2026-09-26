import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Path

from backend.shared.auth import get_current_user
from backend.modules.caregiver.schemas import (
    InviteCreateRequest,
    InviteAcceptRequest,
    CaregiverPatientLinkResponse,
    DashboardResponse,
    NoteCreateRequest,
    NoteResponse,
    AlertItem,
    ChatQueryRequest,
    ChatResponse,
)
from backend.modules.caregiver import invite_service
from backend.modules.caregiver import dashboard_service
from backend.modules.caregiver import chat_assistant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/caregiver", tags=["Caregiver Coordination & Assistant"])


# ==========================================
# 1. INVITATION & ACCESS CONTROL ENDPOINTS
# ==========================================

@router.post(
    "/invite",
    response_model=CaregiverPatientLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Caregiver Invitation",
    description="Generates a secure time-limited invitation token linking a caregiver to a patient.",
)
async def create_caregiver_invite(
    payload: InviteCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    # Verify current user has permission for this patient (e.g. is patient or admin)
    user_id = current_user.get("id")
    # For demo convenience, allow logged in user
    link = await invite_service.create_invite(
        patient_id=payload.patient_id,
        caregiver_email=payload.caregiver_email,
        caregiver_name=payload.caregiver_name,
        permissions=payload.permissions,
        expires_in_days=payload.expires_in_days,
    )
    return link


@router.post(
    "/invite/accept",
    response_model=CaregiverPatientLinkResponse,
    summary="Accept Caregiver Invitation",
    description="Accepts an invitation token and establishes caregiver-patient link.",
)
async def accept_caregiver_invite(
    payload: InviteAcceptRequest,
    current_user: dict = Depends(get_current_user),
):
    caregiver_id = payload.caregiver_id or current_user.get("id")
    caregiver_name = payload.caregiver_name or current_user.get("name")
    
    link = await invite_service.accept_invite(
        token=payload.invite_token,
        caregiver_id=caregiver_id,
        caregiver_name=caregiver_name,
    )
    return link


@router.delete(
    "/invite/{link_id}",
    summary="Revoke Caregiver Access",
    description="Revokes an active or pending caregiver-patient relationship.",
)
async def revoke_caregiver_invite(
    link_id: str = Path(..., description="ID of the caregiver link to revoke"),
    current_user: dict = Depends(get_current_user),
):
    success = await invite_service.revoke_access(
        link_id=link_id,
        requester_id=current_user.get("id", "caregiver-201"),
    )
    return {"message": "Access revoked successfully.", "link_id": link_id, "success": success}


@router.get(
    "/invite/list/{patient_id}",
    response_model=List[CaregiverPatientLinkResponse],
    summary="List Caregivers for Patient",
)
async def list_caregivers(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await invite_service.list_linked_caregivers(patient_id=patient_id)


@router.get(
    "/patients",
    response_model=List[CaregiverPatientLinkResponse],
    summary="List Linked Patients for Caregiver",
)
async def list_patients(
    current_user: dict = Depends(get_current_user),
):
    caregiver_id = current_user.get("id", "caregiver-201")
    return await invite_service.list_linked_patients(caregiver_id=caregiver_id)


# ==========================================
# 2. CAREGIVER DASHBOARD ENDPOINTS
# ==========================================

@router.get(
    "/dashboard/{patient_id}",
    response_model=DashboardResponse,
    summary="Get Caregiver Coordination Dashboard",
    description="Consolidated payload including adherence %, dose history, upcoming doses, alerts, and notes.",
)
async def get_caregiver_dashboard(
    patient_id: str = Path(..., description="Target patient ID"),
    current_user: dict = Depends(get_current_user),
):
    requester_id = current_user.get("id", "caregiver-201")
    return await dashboard_service.get_dashboard(patient_id=patient_id, requester_id=requester_id)


@router.post(
    "/prescription",
    status_code=status.HTTP_201_CREATED,
    summary="Upload / Apply Clinical Prescription",
    description="Loads a formal doctor prescription, dynamically deriving active medications and schedule slots.",
)
async def upload_prescription_endpoint(
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    patient_id = payload.get("patient_id", "patient-101")
    return await dashboard_service.load_patient_prescription(patient_id=patient_id, prescription_data=payload)


@router.get(
    "/prescription/{patient_id}",
    summary="Get Prescriptions for Patient",
    description="Returns all active and historical clinical prescriptions for the patient.",
)
async def get_patient_prescriptions_endpoint(
    patient_id: str = Path(..., description="Target patient ID"),
    current_user: dict = Depends(get_current_user),
):
    from backend.shared.database import db
    return db.prescriptions.get(patient_id, [])


@router.post(
    "/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Shared Patient Note",
    description="Creates a shared note visible to caregiver and patient. Requires 'read_respond' permission.",
)
async def create_shared_note(
    payload: NoteCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    return await dashboard_service.create_note(
        patient_id=payload.patient_id,
        content=payload.content,
        author=current_user,
    )


@router.get(
    "/notes/{patient_id}",
    response_model=List[NoteResponse],
    summary="Get Shared Notes for Patient",
)
async def get_patient_notes(
    patient_id: str = Path(..., description="Target patient ID"),
    current_user: dict = Depends(get_current_user),
):
    return await dashboard_service.get_notes(patient_id=patient_id)


@router.get(
    "/alerts/{patient_id}",
    response_model=List[AlertItem],
    summary="Get Missed Dose Alerts & Escalations",
)
async def get_patient_alerts(
    patient_id: str = Path(..., description="Target patient ID"),
    current_user: dict = Depends(get_current_user),
):
    return await dashboard_service.get_alerts(patient_id=patient_id)


# ==========================================
# 3. RAG-GROUNDED CHAT ASSISTANT
# ==========================================

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Grounded Medication Chat Assistant",
    description="RAG-grounded natural language Q&A across prescription explanations, timetable schedule, and risk interaction checks.",
)
async def chat_assistant_endpoint(
    payload: ChatQueryRequest,
    current_user: dict = Depends(get_current_user),
):
    response = await chat_assistant_service.answer_medication_query(
        patient_id=payload.patient_id,
        query=payload.query,
        user_context=current_user,
    )
    return response
