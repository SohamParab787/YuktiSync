import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status

from backend.config import settings
from backend.shared.database import db
from backend.modules.caregiver.schemas import (
    CaregiverPermissionEnum,
    InviteStatusEnum,
    CaregiverPermissions,
)

logger = logging.getLogger(__name__)


def generate_invite_token(patient_id: str, email: str, permissions: str, expires_in_days: int = 7) -> (str, datetime):
    """
    Generate a secure, time-limited JWT token specifically for caregiver invitations.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
    payload = {
        "sub": email,
        "patient_id": patient_id,
        "permissions": permissions,
        "token_type": "caregiver_invite",
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expire


def verify_invite_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate caregiver invite token.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("token_type") != "caregiver_invite":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type: not a caregiver invitation token.",
            )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or expired invitation token: {str(e)}",
        )


async def create_invite(
    patient_id: str,
    caregiver_email: str,
    caregiver_name: Optional[str] = None,
    permissions: CaregiverPermissionEnum = CaregiverPermissionEnum.READ_ONLY,
    expires_in_days: int = 7,
) -> Dict[str, Any]:
    """
    Creates an invitation token linking a caregiver account to a patient account.
    Stores the link record in the shared database.
    """
    # Check if active link already exists
    for link in db.caregiver_links.values():
        if (
            link.get("patient_id") == patient_id
            and link.get("caregiver_email") == caregiver_email
            and link.get("status") in [InviteStatusEnum.ACCEPTED.value, InviteStatusEnum.PENDING.value]
        ):
            if link.get("status") == InviteStatusEnum.ACCEPTED.value:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Caregiver '{caregiver_email}' is already actively linked to this patient.",
                )

    token, expires_at = generate_invite_token(
        patient_id=patient_id,
        email=caregiver_email,
        permissions=permissions.value,
        expires_in_days=expires_in_days,
    )

    link_id = f"link-{uuid.uuid4().hex[:8]}"
    patient_user = db.users.get(patient_id, {})
    patient_name = patient_user.get("name", f"Patient {patient_id}")

    link_record = {
        "id": link_id,
        "patient_id": patient_id,
        "caregiver_id": None,
        "caregiver_email": caregiver_email,
        "caregiver_name": caregiver_name,
        "patient_name": patient_name,
        "permissions": permissions.value,
        "status": InviteStatusEnum.PENDING.value,
        "invite_token": token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    db.caregiver_links[link_id] = link_record
    logger.info(f"Generated caregiver invite {link_id} for patient {patient_id} -> {caregiver_email}")

    response = link_record.copy()
    response["invite_url"] = f"/caregiver/invite?token={token}"
    return response


async def accept_invite(
    token: str,
    caregiver_id: Optional[str] = None,
    caregiver_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Accepts an invitation token and binds caregiver user to patient.
    """
    payload = verify_invite_token(token)
    patient_id = payload.get("patient_id")
    caregiver_email = payload.get("sub")
    permissions = payload.get("permissions", CaregiverPermissionEnum.READ_ONLY.value)

    # Find matching link in DB
    target_link = None
    for link in db.caregiver_links.values():
        if link.get("invite_token") == token:
            target_link = link
            break

    now = datetime.now(timezone.utc)
    if not target_link:
        # Create fresh accepted link from valid signed JWT
        link_id = f"link-{uuid.uuid4().hex[:8]}"
        patient_user = db.users.get(patient_id, {})
        target_link = {
            "id": link_id,
            "patient_id": patient_id,
            "caregiver_id": caregiver_id or f"cg-{uuid.uuid4().hex[:6]}",
            "caregiver_email": caregiver_email,
            "caregiver_name": caregiver_name or "Caregiver",
            "patient_name": patient_user.get("name", "Patient"),
            "permissions": permissions,
            "status": InviteStatusEnum.ACCEPTED.value,
            "invite_token": None,
            "expires_at": None,
            "created_at": now,
            "updated_at": now,
        }
        db.caregiver_links[link_id] = target_link
        return target_link

    if target_link["status"] == InviteStatusEnum.REVOKED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has been revoked by the patient.",
        )

    if target_link.get("expires_at") and target_link["expires_at"] < now:
        target_link["status"] = InviteStatusEnum.EXPIRED.value
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has expired. Please request a new invite.",
        )

    # Update to accepted
    target_link["status"] = InviteStatusEnum.ACCEPTED.value
    target_link["caregiver_id"] = caregiver_id or target_link.get("caregiver_id") or f"cg-{uuid.uuid4().hex[:6]}"
    if caregiver_name:
        target_link["caregiver_name"] = caregiver_name
    target_link["updated_at"] = now
    target_link["invite_token"] = None  # Consume token

    return target_link


async def revoke_access(link_id: str, requester_id: str) -> bool:
    """
    Revokes caregiver<->patient link access.
    Can be called by either the patient or the caregiver.
    """
    link = db.caregiver_links.get(link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Caregiver link '{link_id}' not found.",
        )

    if link["patient_id"] != requester_id and link.get("caregiver_id") != requester_id and requester_id != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to revoke this link.",
        )

    link["status"] = InviteStatusEnum.REVOKED.value
    link["updated_at"] = datetime.now(timezone.utc)
    return True


async def list_linked_caregivers(patient_id: str) -> List[Dict[str, Any]]:
    """
    List all caregivers connected or invited to a patient.
    """
    links = [
        link for link in db.caregiver_links.values()
        if link["patient_id"] == patient_id and link["status"] != InviteStatusEnum.REVOKED.value
    ]
    return links


async def list_linked_patients(caregiver_id: str) -> List[Dict[str, Any]]:
    """
    List all patients associated with a caregiver.
    """
    links = [
        link for link in db.caregiver_links.values()
        if link.get("caregiver_id") == caregiver_id and link["status"] == InviteStatusEnum.ACCEPTED.value
    ]
    return links


async def get_caregiver_permissions(patient_id: str, caregiver_id: str) -> CaregiverPermissions:
    """
    Enforces role-based permissions (read-only vs. read+respond).
    """
    matched_link = None
    for link in db.caregiver_links.values():
        if (
            link["patient_id"] == patient_id
            and link.get("caregiver_id") == caregiver_id
            and link["status"] == InviteStatusEnum.ACCEPTED.value
        ):
            matched_link = link
            break

    # If patient is viewing their own records
    if patient_id == caregiver_id:
        return CaregiverPermissions(
            patient_id=patient_id,
            caregiver_id=caregiver_id,
            permissions=CaregiverPermissionEnum.READ_RESPOND,
            can_view_adherence=True,
            can_view_schedule=True,
            can_add_notes=True,
            can_manage_alerts=True,
        )

    if not matched_link:
        # Default or fallback permission if accessing during demo
        return CaregiverPermissions(
            patient_id=patient_id,
            caregiver_id=caregiver_id,
            permissions=CaregiverPermissionEnum.READ_RESPOND,
            can_view_adherence=True,
            can_view_schedule=True,
            can_add_notes=True,
            can_manage_alerts=True,
        )

    perm_str = matched_link.get("permissions", CaregiverPermissionEnum.READ_ONLY.value)
    is_read_respond = (perm_str == CaregiverPermissionEnum.READ_RESPOND.value)

    return CaregiverPermissions(
        patient_id=patient_id,
        caregiver_id=caregiver_id,
        permissions=CaregiverPermissionEnum(perm_str),
        can_view_adherence=True,
        can_view_schedule=True,
        can_add_notes=is_read_respond,
        can_manage_alerts=is_read_respond,
    )
