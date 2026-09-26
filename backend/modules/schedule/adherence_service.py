"""
Schedule Adherence Service (PERSON 2 MODULE)
Public interface for real-time adherence calculation and dose history tracking.
"""

from typing import Dict, Any, List
from backend.shared.database import db


async def get_adherence_summary(patient_id: str) -> Dict[str, Any]:
    """
    Public Service Function for Person 2:
    Returns adherence rate, total scheduled, taken count, missed count, upcoming count,
    and recent dose history logs for the given patient.
    TODO for Person 2: Hook up dynamic calculation across historical date ranges.
    """
    logs: List[Dict[str, Any]] = db.dose_logs.get(patient_id, [])
    
    taken_count = sum(1 for log in logs if log.get("status") == "taken")
    missed_count = sum(1 for log in logs if log.get("status") == "missed")
    upcoming_count = sum(1 for log in logs if log.get("status") == "upcoming")
    
    past_doses = taken_count + missed_count
    adherence_rate = round((taken_count / past_doses * 100), 1) if past_doses > 0 else 100.0

    return {
        "patient_id": patient_id,
        "adherence_rate": adherence_rate,
        "total_scheduled": len(logs),
        "taken_count": taken_count,
        "missed_count": missed_count,
        "upcoming_count": upcoming_count,
        "recent_doses": logs,
    }
