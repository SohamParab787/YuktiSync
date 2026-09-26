"""
Schedule Escalation Service (PERSON 2 MODULE)

Handles missed-dose detection, escalation levels, caregiver alerts,
and retrieval of unresolved patient escalations.
"""

import uuid
import httpx

from datetime import datetime
from typing import Dict, Any, Optional, List

from backend.shared.models.dose_log import DoseLog
from backend.shared.database import get_db


class EscalationService:
    """
    Handles the missed-dose escalation workflow.

    Escalation flow:

        Missed Dose
             ↓
        INFO alert
             ↓
        2 missed doses → WARNING
             ↓
        3+ missed doses → CRITICAL
             ↓
        Caregiver notification

    Every escalation event is stored for auditing.
    """

    def __init__(self, db=None):
        self.db = db or get_db()

    def count_consecutive_missed_doses(
        self,
        user_id: str
    ) -> List[DoseLog]:
        """
        Returns the current sequence of consecutive missed/skipped doses.
        """

        all_doses = self.db.get_dose_logs_by_user(user_id)

        now_str = datetime.now().isoformat()

        past_and_current_doses = [
            dose
            for dose in all_doses
            if (
                dose.scheduled_time <= now_str
                and dose.status not in ["pending", "upcoming"]
            )
        ]

        past_and_current_doses.sort(
            key=lambda dose: dose.scheduled_time,
            reverse=True
        )

        consecutive_missed = []

        for dose in past_and_current_doses:

            if dose.status in ["missed", "skipped"]:
                consecutive_missed.append(dose)
            else:
                # Taken/delayed dose breaks the sequence.
                break

        return consecutive_missed

    async def check_and_escalate(
        self,
        user_id: str,
        caregiver_api_url: str = (
            "http://localhost:8000/api/caregiver/alert"
        )
    ) -> Dict[str, Any]:
        """
        Evaluates missed-dose history and triggers the escalation ladder.
        """

        missed_doses = self.count_consecutive_missed_doses(user_id)

        count = len(missed_doses)

        # No missed doses
        if count == 0:
            return {
                "user_id": user_id,
                "consecutive_missed": 0,
                "escalated": False,
                "alert_level": "NONE",
                "message": (
                    "No active missed doses requiring escalation."
                )
            }

        # One missed dose → patient-level INFO
        if count == 1:

            record = {
                "id": f"esc-{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "alert_level": "INFO",
                "consecutive_missed": 1,
                "medications": [
                    missed_doses[0].medication_name
                ],
                "timestamp": datetime.now().isoformat(),
                "message": (
                    f"Patient missed 1 dose "
                    f"({missed_doses[0].medication_name}). "
                    "Patient notification issued."
                )
            }

            self.db.record_escalation(record)

            return {
                "user_id": user_id,
                "consecutive_missed": 1,
                "escalated": False,
                "alert_level": "INFO",
                "message": record["message"],
                "event_id": record["id"]
            }

        # 2 missed → WARNING
        # 3+ missed → CRITICAL
        alert_level = (
            "CRITICAL"
            if count >= 3
            else "WARNING"
        )

        med_names = list({
            dose.medication_name
            for dose in missed_doses
        })

        payload = {
            "user_id": user_id,
            "alert_level": alert_level,
            "consecutive_missed_count": count,
            "medications": med_names,
            "timestamp": datetime.now().isoformat(),
            "message": (
                f"{'URGENT: ' if alert_level == 'CRITICAL' else ''}"
                f"Patient has missed {count} consecutive doses "
                f"({', '.join(med_names)})."
            )
        }

        escalated_success = False
        api_response_msg = ""

        try:

            async with httpx.AsyncClient(
                timeout=5.0
            ) as client:

                response = await client.post(
                    caregiver_api_url,
                    json=payload
                )

                if response.status_code in [200, 201, 202]:

                    escalated_success = True
                    api_response_msg = (
                        "Caregiver alerted successfully."
                    )

                else:

                    api_response_msg = (
                        "Caregiver API returned status "
                        f"{response.status_code}."
                    )

        except Exception as error:

            api_response_msg = (
                "HTTP call to Caregiver API failed: "
                f"{str(error)}"
            )

        record = {
            "id": f"esc-{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "alert_level": alert_level,
            "consecutive_missed": count,
            "medications": med_names,
            "timestamp": payload["timestamp"],
            "message": payload["message"],
            "caregiver_status": api_response_msg
        }

        self.db.record_escalation(record)

        return {
            "user_id": user_id,
            "consecutive_missed": count,
            "escalated": True,
            "alert_level": alert_level,
            "message": payload["message"],
            "caregiver_api_status": api_response_msg,
            "event_id": record["id"]
        }


async def get_patient_escalations(
    patient_id: str
) -> List[Dict[str, Any]]:
    """
    Backward-compatible public interface.

    Retrieves unresolved alerts for a patient.
    """

    service = EscalationService()

    alerts = [
        alert
        for alert in service.db.alerts
        if (
            alert.get("patient_id") == patient_id
            and not alert.get("is_resolved", False)
        )
    ]

    return alerts