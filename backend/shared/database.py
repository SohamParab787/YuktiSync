import threading
from typing import List, Dict, Optional
from datetime import datetime
from backend.shared.models.medication import Medication
from backend.shared.models.dose_log import DoseLog

class InMemoryDatabase:
    """
    Thread-safe datastore for medications, dose logs, activity logs, and escalation events.
    Can be expanded to sync with MongoDB (Motor) if MONGO_URI is set.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.medications: Dict[str, Medication] = {}
        self.dose_logs: Dict[str, DoseLog] = {}
        self.users: Dict[str, dict] = {}
        self.caregivers: Dict[str, dict] = {}
        self.prescriptions: Dict[str, dict] = {}
        self.risk_alerts: Dict[str, dict] = {}
        self.escalation_logs: List[dict] = []
        self.activity_logs: List[dict] = []

    def clear(self):
        with self._lock:
            self.medications.clear()
            self.dose_logs.clear()
            self.users.clear()
            self.caregivers.clear()
            self.prescriptions.clear()
            self.risk_alerts.clear()
            self.escalation_logs.clear()
            self.activity_logs.clear()

    # Medication methods
    def save_medication(self, medication: Medication) -> Medication:
        with self._lock:
            self.medications[medication.id] = medication
            return medication

    def get_medication(self, med_id: str) -> Optional[Medication]:
        with self._lock:
            return self.medications.get(med_id)

    def get_medications_by_user(self, user_id: str) -> List[Medication]:
        with self._lock:
            return [m for m in self.medications.values() if m.user_id == user_id]

    # DoseLog methods
    def save_dose_log(self, dose_log: DoseLog) -> DoseLog:
        with self._lock:
            self.dose_logs[dose_log.id] = dose_log
            return dose_log

    def get_dose_log(self, dose_id: str) -> Optional[DoseLog]:
        with self._lock:
            return self.dose_logs.get(dose_id)

    def get_dose_logs_by_user(self, user_id: str) -> List[DoseLog]:
        with self._lock:
            return [d for d in self.dose_logs.values() if d.user_id == user_id]

    def update_dose_log(self, dose_log: DoseLog) -> DoseLog:
        with self._lock:
            self.dose_logs[dose_log.id] = dose_log
            return dose_log

    # Activity & Escalation Log methods
    def record_activity(self, user_id: str, dose_id: str, medication_name: str, action: str, details: Optional[str] = None):
        with self._lock:
            activity = {
                "id": f"act-{len(self.activity_logs) + 1}",
                "user_id": user_id,
                "dose_id": dose_id,
                "medication_name": medication_name,
                "action": action, # "Marked as Taken", "Delayed", "Skipped", etc.
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
            self.activity_logs.insert(0, activity) # latest first
            return activity

    def get_activities(self, user_id: str, limit: int = 10) -> List[dict]:
        with self._lock:
            return [a for a in self.activity_logs if a.get("user_id") == user_id][:limit]

    def record_escalation(self, event: dict):
        with self._lock:
            self.escalation_logs.insert(0, event)
            return event

    def get_escalations(self, user_id: str, limit: int = 10) -> List[dict]:
        with self._lock:
            return [e for e in self.escalation_logs if e.get("user_id") == user_id][:limit]

db = InMemoryDatabase()

def get_db() -> InMemoryDatabase:
    return db
