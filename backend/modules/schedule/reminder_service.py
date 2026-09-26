from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from backend.shared.models.dose_log import DoseLog
from backend.shared.database import get_db

class ReminderService:
    def __init__(self, db=None):
        self.db = db or get_db()

    def get_upcoming_reminders(self, user_id: str, lookahead_minutes: int = 30) -> List[Dict[str, Any]]:
        """
        Finds upcoming doses scheduled within the lookahead_minutes window from current time.
        """
        now = datetime.now()
        window_end = now + timedelta(minutes=lookahead_minutes)

        user_doses = self.db.get_dose_logs_by_user(user_id)
        reminders = []

        for dose in user_doses:
            if dose.status == "upcoming":
                try:
                    sched_dt = datetime.fromisoformat(dose.scheduled_time)
                    if now <= sched_dt <= window_end:
                        time_until_seconds = int((sched_dt - now).total_seconds())
                        reminders.append({
                            "dose_id": dose.id,
                            "medication_id": dose.medication_id,
                            "medication_name": dose.medication_name,
                            "dosage": dose.dosage,
                            "scheduled_time": dose.scheduled_time,
                            "time_until_seconds": max(0, time_until_seconds),
                            "instructions": dose.instructions,
                            "title": f"Upcoming Dose: {dose.medication_name}",
                            "message": f"Time to take {dose.medication_name} ({dose.dosage}) scheduled at {sched_dt.strftime('%H:%M')}."
                        })
                except ValueError:
                    pass

        return reminders

    def trigger_dose_reminder(self, dose_id: str) -> Dict[str, Any]:
        """
        Generates notification payload for a specific dose.
        """
        dose = self.db.get_dose_log(dose_id)
        if not dose:
            raise ValueError(f"Dose '{dose_id}' not found.")

        return {
            "dose_id": dose.id,
            "user_id": dose.user_id,
            "medication_name": dose.medication_name,
            "dosage": dose.dosage,
            "scheduled_time": dose.scheduled_time,
            "status": dose.status,
            "instructions": dose.instructions,
            "notification": {
                "title": f"Reminder: Take {dose.medication_name}",
                "body": f"It's time to take your {dose.dosage} dose of {dose.medication_name}." + (f" ({dose.instructions})" if dose.instructions else ""),
                "timestamp": datetime.now().isoformat()
            }
        }
