"""
Schedule Generator Service (PERSON 2 MODULE)
Public interface for schedule timetable generation and upcoming doses.
"""

from typing import List, Dict, Any
from backend.shared.database import db


async def get_upcoming_doses(patient_id: str) -> List[Dict[str, Any]]:
    """
    Public Service Function for Person 2:
    Retrieves upcoming scheduled doses for the day/week.
    TODO for Person 2: Implement dynamic chron-based dosage generator based on prescription instructions.
    """
    logs = db.dose_logs.get(patient_id, [])
    return [log for log in logs if log.get("status") == "upcoming"]


async def get_patient_schedule(patient_id: str) -> List[Dict[str, Any]]:
    """
    Public Service Function for Person 2:
    Retrieves all scheduled slots for patient.
    """
    return db.dose_logs.get(patient_id, [])
