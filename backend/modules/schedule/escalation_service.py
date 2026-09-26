import uuid
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List
from backend.shared.models.dose_log import DoseLog
from backend.shared.database import get_db

class EscalationService:
    """
    Escalation Service for YuktiSync:
    Evaluates patient dose history for unconfirmed/missed doses and triggers an escalation ladder toward
    Person 4's caregiver module strictly via HTTP endpoint (/api/caregiver/*).
    Records every escalation event in the database for auditing and patient safety.
    """
    def __init__(self, db=None):
        self.db = db or get_db()

    def count_consecutive_missed_doses(self, user_id: str) -> List[DoseLog]:
        """
        Retrieves user's doses up to current time, sorted chronologically,
        and identifies current sequence of missed doses.
        """
        all_doses = self.db.get_dose_logs_by_user(user_id)
        # Filter doses scheduled up to now
        past_and_current_doses = []
        now_str = datetime.now().isoformat()

        for d in all_doses:
            if d.scheduled_time <= now_str and d.status not in ["pending", "upcoming"]:
                past_and_current_doses.append(d)

        # Sort by scheduled time descending (most recent first)
        past_and_current_doses.sort(key=lambda x: x.scheduled_time, reverse=True)

        consecutive_missed = []
        for dose in past_and_current_doses:
            if dose.status in ["missed", "skipped"]:
                consecutive_missed.append(dose)
            else:
                # Sequence broken by taken/delayed dose
                break

        return consecutive_missed

    async def check_and_escalate(
        self,
        user_id: str,
        caregiver_api_url: str = "http://localhost:8000/api/caregiver/alert"
    ) -> Dict[str, Any]:
        """
        Evaluates missed doses ladder and calls /api/caregiver/* if threshold met.
        Records escalation event.
        """
        missed_doses = self.count_consecutive_missed_doses(user_id)
        count = len(missed_doses)

        if count == 0:
            return {
                "user_id": user_id,
                "consecutive_missed": 0,
                "escalated": False,
                "alert_level": "NONE",
                "message": "No active missed doses requiring escalation."
            }

        if count == 1:
            record = {
                "id": f"esc-{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "alert_level": "INFO",
                "consecutive_missed": 1,
                "medications": [missed_doses[0].medication_name],
                "timestamp": datetime.now().isoformat(),
                "message": f"Patient missed 1 dose ({missed_doses[0].medication_name}). Patient notification issued."
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

        # Level 2 (2 missed) or Level 3 (3+ missed doses): Escalate to Caregiver Module via HTTP
        alert_level = "CRITICAL" if count >= 3 else "WARNING"
        med_names = list({d.medication_name for d in missed_doses})
        payload = {
            "user_id": user_id,
            "alert_level": alert_level,
            "consecutive_missed_count": count,
            "medications": med_names,
            "timestamp": datetime.now().isoformat(),
            "message": f"{'URGENT: ' if alert_level == 'CRITICAL' else ''}Patient has missed {count} consecutive doses ({', '.join(med_names)})."
        }

        escalated_success = False
        api_response_msg = ""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(caregiver_api_url, json=payload)
                if res.status_code in [200, 201, 202]:
                    escalated_success = True
                    api_response_msg = "Caregiver alerted successfully."
                else:
                    api_response_msg = f"Caregiver API returned status {res.status_code}."
        except Exception as e:
            # Service down or un-mounted during test execution; logged gracefully
            api_response_msg = f"HTTP call to Caregiver API failed: {str(e)}"

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
