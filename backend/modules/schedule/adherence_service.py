from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from backend.shared.models.dose_log import DoseLog
from backend.shared.database import get_db

class AdherenceService:
    """
    Adherence Service for tracking dose statuses (taken/missed/delayed),
    computing daily/weekly adherence statistics, and auto-transitioning overdue doses.
    
    Auto-Transition Strategy:
    MediAdhere employs an on-read check on dose query (in auto_transition_missed_doses),
    ensuring whenever dashboard or schedule endpoints are accessed, any UPCOMING doses
    whose (scheduled_time + grace_period_minutes) has passed are immediately updated to MISSED.
    It also provides `auto_transition_missed_doses` as a function ready to be called by a periodic background runner.
    """
    def __init__(self, db=None):
        self.db = db or get_db()

    def auto_transition_missed_doses(self, user_id: Optional[str] = None, grace_period_minutes: int = 60) -> List[DoseLog]:
        """
        Inspects upcoming doses. If current time is past (scheduled_time + grace_period_minutes),
        transitions status to 'missed'.
        """
        now = datetime.now()
        transitioned = []
        all_doses = self.db.get_dose_logs_by_user(user_id) if user_id else list(self.db.dose_logs.values())

        for dose in all_doses:
            if dose.status == "upcoming":
                try:
                    sched_dt = datetime.fromisoformat(dose.scheduled_time)
                    grace = timedelta(minutes=dose.grace_period_minutes or grace_period_minutes)
                    if now > (sched_dt + grace):
                        dose.status = "missed"
                        self.db.update_dose_log(dose)
                        transitioned.append(dose)
                except ValueError:
                    pass
        return transitioned

    def log_dose_status(
        self,
        dose_id: str,
        status: str,
        taken_at: Optional[str] = None,
        notes: Optional[str] = None
    ) -> DoseLog:
        """
        Logs dose status (taken/missed/delayed).
        If status is 'taken' but taken_at is past scheduled_time + grace_period, automatically flags as 'delayed'.
        """
        dose = self.db.get_dose_log(dose_id)
        if not dose:
            raise ValueError(f"Dose with ID '{dose_id}' not found.")

        target_status = status.lower()
        if target_status not in ["taken", "missed", "delayed", "upcoming"]:
            raise ValueError(f"Invalid status '{status}'. Must be taken, missed, delayed, or upcoming.")

        taken_timestamp = taken_at or datetime.now().isoformat()

        if target_status == "taken":
            try:
                sched_dt = datetime.fromisoformat(dose.scheduled_time)
                actual_dt = datetime.fromisoformat(taken_timestamp)
                grace = timedelta(minutes=dose.grace_period_minutes)
                if actual_dt > (sched_dt + grace):
                    target_status = "delayed"
            except ValueError:
                pass

        dose.status = target_status
        if target_status in ["taken", "delayed"]:
            dose.taken_at = taken_timestamp
        dose.notes = notes or dose.notes

        return self.db.update_dose_log(dose)

    def get_daily_adherence(self, user_id: str, target_date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Computes adherence metrics for a specific day (default: today).
        """
        self.auto_transition_missed_doses(user_id=user_id)

        target_date = target_date_str or date.today().isoformat()
        user_doses = self.db.get_dose_logs_by_user(user_id)

        todays_doses = [
            d for d in user_doses
            if d.scheduled_time.startswith(target_date)
        ]

        total = len(todays_doses)
        taken = sum(1 for d in todays_doses if d.status == "taken")
        missed = sum(1 for d in todays_doses if d.status == "missed")
        delayed = sum(1 for d in todays_doses if d.status == "delayed")
        upcoming = sum(1 for d in todays_doses if d.status == "upcoming")

        due_total = taken + missed + delayed
        if due_total > 0:
            percentage = round(((taken + (0.5 * delayed)) / due_total) * 100.0, 1)
        else:
            percentage = 100.0

        return {
            "user_id": user_id,
            "date": target_date,
            "period": "today",
            "total_doses": total,
            "taken_doses": taken,
            "missed_doses": missed,
            "delayed_doses": delayed,
            "upcoming_doses": upcoming,
            "adherence_percentage": percentage
        }

    def get_weekly_adherence(self, user_id: str, start_date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Computes daily breakdown for a 7-day window and overall weekly percentage.
        """
        self.auto_transition_missed_doses(user_id=user_id)

        start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else (date.today() - timedelta(days=6))
        end_d = start_d + timedelta(days=6)

        user_doses = self.db.get_dose_logs_by_user(user_id)

        daily_breakdown = []
        total_taken = 0
        total_missed = 0
        total_delayed = 0
        total_upcoming = 0

        for day_offset in range(7):
            curr_date_str = (start_d + timedelta(days=day_offset)).isoformat()
            day_doses = [d for d in user_doses if d.scheduled_time.startswith(curr_date_str)]

            d_total = len(day_doses)
            d_taken = sum(1 for d in day_doses if d.status == "taken")
            d_missed = sum(1 for d in day_doses if d.status == "missed")
            d_delayed = sum(1 for d in day_doses if d.status == "delayed")
            d_upcoming = sum(1 for d in day_doses if d.status == "upcoming")

            d_due = d_taken + d_missed + d_delayed
            d_pct = round(((d_taken + (0.5 * d_delayed)) / d_due) * 100.0, 1) if d_due > 0 else 100.0

            total_taken += d_taken
            total_missed += d_missed
            total_delayed += d_delayed
            total_upcoming += d_upcoming

            daily_breakdown.append({
                "date": curr_date_str,
                "total_doses": d_total,
                "taken_doses": d_taken,
                "missed_doses": d_missed,
                "delayed_doses": d_delayed,
                "upcoming_doses": d_upcoming,
                "adherence_percentage": d_pct,
                "doses": [d.model_dump() for d in day_doses]
            })

        overall_due = total_taken + total_missed + total_delayed
        overall_pct = round(((total_taken + (0.5 * total_delayed)) / overall_due) * 100.0, 1) if overall_due > 0 else 100.0

        return {
            "user_id": user_id,
            "view_type": "weekly",
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "total_doses": total_taken + total_missed + total_delayed + total_upcoming,
            "taken_doses": total_taken,
            "missed_doses": total_missed,
            "delayed_doses": total_delayed,
            "upcoming_doses": total_upcoming,
            "overall_adherence_percentage": overall_pct,
            "daily_breakdown": daily_breakdown
        }
