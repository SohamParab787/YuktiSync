import threading
from typing import List, Dict, Optional
from backend.shared.models.medication import Medication
from backend.shared.models.dose_log import DoseLog

class InMemoryDatabase:
    """
    Thread-safe datastore for medications and dose logs.
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

    def clear(self):
        with self._lock:
            self.medications.clear()
            self.dose_logs.clear()
            self.users.clear()
            self.caregivers.clear()
            self.prescriptions.clear()
            self.risk_alerts.clear()

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

db = InMemoryDatabase()

def get_db() -> InMemoryDatabase:
    return db
