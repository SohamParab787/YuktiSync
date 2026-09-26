"""
Schedule Escalation Service (PERSON 2 MODULE)
Public interface for missed dose escalations and alerts.
"""

from typing import List, Dict, Any
from backend.shared.database import db


async def get_patient_escalations(patient_id: str) -> List[Dict[str, Any]]:
    """
    Public Service Function for Person 2:
    Retrieves unresolved missed-dose escalations and threshold notifications for patient.
    TODO for Person 2: Implement SMS/Push notification escalation pipeline and automated resolution triggers.
    """
    alerts = [a for a in db.alerts if a.get("patient_id") == patient_id and not a.get("is_resolved", False)]
    return alerts
