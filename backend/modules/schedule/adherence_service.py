from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from backend.shared.models.dose_log import DoseLog
from backend.shared.database import get_db

class AdherenceService:
    """
    Adherence Service for YuktiSync:
    Tracks dose statuses (pending/upcoming, taken, delayed, missed, skipped),
    computes adherence analytics, handles anti-stacking safety checks,
    and logs patient medication activities.
    """
    def __init__(self, db=None):
        self.db = db or get_db()

    def auto_transition_missed_doses(self, user_id: Optional[str] = None, grace_period_minutes: int = 60) -> List[DoseLog]:
        """
        Inspects pending/upcoming doses. If current time is past (scheduled_time + grace_period_minutes),
        transitions status to 'missed'.
        """
        now = datetime.now()
        transitioned = []
        all_doses = self.db.get_dose_logs_by_user(user_id) if user_id else list(self.db.dose_logs.values())

        for dose in all_doses:
            if dose.status in ["pending", "upcoming"]:
                try:
                    sched_dt = datetime.fromisoformat(dose.scheduled_time)
                    grace = timedelta(minutes=dose.grace_period_minutes or grace_period_minutes)
                    if now > (sched_dt + grace):
                        dose.status = "missed"
                        self.db.update_dose_log(dose)
                        self.db.record_activity(
                            user_id=dose.user_id,
                            dose_id=dose.id,
                            medication_name=dose.medication_name,
                            action="Auto-marked as Missed",
                            details=f"Dose was unconfirmed after {dose.grace_period_minutes or grace_period_minutes} min grace window."
                        )
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
        Logs dose status (taken/missed/delayed/skipped).
        If status is 'taken' but taken_at is past scheduled_time + grace_period, automatically flags as 'delayed'.
        Records event in activity history.
        """
        dose = self.db.get_dose_log(dose_id)
        if not dose:
            raise ValueError(f"Dose with ID '{dose_id}' not found.")

        target_status = status.lower()
        if target_status not in ["taken", "missed", "delayed", "skipped", "pending", "upcoming"]:
            raise ValueError(f"Invalid status '{status}'. Must be taken, missed, delayed, skipped, or pending.")

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

        updated = self.db.update_dose_log(dose)

        # Log activity
        action_map = {
            "taken": "Marked as Taken",
            "delayed": "Marked as Delayed",
            "missed": "Marked as Missed",
            "skipped": "Marked as Skipped",
            "pending": "Reset to Pending"
        }
        self.db.record_activity(
            user_id=dose.user_id,
            dose_id=dose.id,
            medication_name=dose.medication_name,
            action=action_map.get(target_status, f"Status updated to {target_status}"),
            details=f"Dosage: {dose.dosage} | Scheduled: {dose.scheduled_time} | Notes: {notes or 'None'}"
        )

        return updated

    def evaluate_anti_stacking(self, user_id: str, dose_id: Optional[str] = None, medication_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Anti-Stacking & Missed-Dose Safety Rule:
        Compares current time with the next scheduled dose for this medication.
        Returns safety recommendation: SAFE TO TAKE, WAIT / SKIP, or CONSULT PROFESSIONAL.
        Never automatically modifies prescribed dosage.
        """
        all_doses = self.db.get_dose_logs_by_user(user_id)
        target_med = medication_name

        if dose_id:
            curr_dose = self.db.get_dose_log(dose_id)
            if curr_dose:
                target_med = curr_dose.medication_name

        if not target_med and all_doses:
            target_med = all_doses[0].medication_name

        if not target_med:
            return {
                "status": "SAFE TO TAKE",
                "recommendation": "No scheduled doses found to conflict with.",
                "hours_until_next_dose": None,
                "next_scheduled_time": None,
                "stacking_risk_detected": False,
                "disclaimer": "Medication decisions should follow prescribed instructions or professional guidance. Never automatically change your prescribed dosage."
            }

        now = datetime.now()
        # Find next upcoming dose for the same medication
        future_doses = []
        missed_count = 0

        for d in all_doses:
            if d.medication_name.lower() == target_med.lower():
                if d.status in ["missed", "skipped"]:
                    missed_count += 1
                try:
                    s_dt = datetime.fromisoformat(d.scheduled_time)
                    if s_dt > now and d.status in ["pending", "upcoming"]:
                        future_doses.append((s_dt, d))
                except ValueError:
                    pass

        future_doses.sort(key=lambda x: x[0])

        if missed_count >= 2:
            return {
                "status": "CONSULT PROFESSIONAL",
                "recommendation": f"You have missed {missed_count} doses of {target_med}. Please consult your physician or pharmacist before resuming this medication to avoid adverse effects or complications.",
                "hours_until_next_dose": (future_doses[0][0] - now).total_seconds() / 3600.0 if future_doses else None,
                "next_scheduled_time": future_doses[0][1].scheduled_time if future_doses else None,
                "stacking_risk_detected": True,
                "disclaimer": "Medication decisions should follow prescribed instructions or professional guidance. Never automatically change your prescribed dosage."
            }

        if not future_doses:
            return {
                "status": "SAFE TO TAKE",
                "recommendation": f"No immediate next dose scheduled for {target_med}. Safe to take this dose as prescribed.",
                "hours_until_next_dose": None,
                "next_scheduled_time": None,
                "stacking_risk_detected": False,
                "disclaimer": "Medication decisions should follow prescribed instructions or professional guidance. Never automatically change your prescribed dosage."
            }

        next_dt, next_dose_obj = future_doses[0]
        hours_diff = (next_dt - now).total_seconds() / 3600.0
        time_formatted = next_dt.strftime("%I:%M %p")

        # Threshold: if next dose is less than 4 hours away, risk of drug stacking
        if hours_diff < 4.0:
            return {
                "status": "WAIT / SKIP",
                "recommendation": f"Your next scheduled dose of {target_med} is only {hours_diff:.1f} hours away at {time_formatted}. Taking this dose now may cause hazardous drug stacking. Skip this missed dose and take your next dose at the regular time.",
                "hours_until_next_dose": round(hours_diff, 1),
                "next_scheduled_time": next_dose_obj.scheduled_time,
                "stacking_risk_detected": True,
                "disclaimer": "Medication decisions should follow prescribed instructions or professional guidance. Never automatically change your prescribed dosage."
            }
        else:
            return {
                "status": "SAFE TO TAKE",
                "recommendation": f"It is safe to take your dose now. Your next scheduled dose of {target_med} is {hours_diff:.1f} hours away at {time_formatted}. Do not exceed your prescribed dosage.",
                "hours_until_next_dose": round(hours_diff, 1),
                "next_scheduled_time": next_dose_obj.scheduled_time,
                "stacking_risk_detected": False,
                "disclaimer": "Medication decisions should follow prescribed instructions or professional guidance. Never automatically change your prescribed dosage."
            }

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
        missed = sum(1 for d in todays_doses if d.status in ["missed", "skipped"])
        delayed = sum(1 for d in todays_doses if d.status == "delayed")
        upcoming = sum(1 for d in todays_doses if d.status in ["pending", "upcoming"])

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
            d_missed = sum(1 for d in day_doses if d.status in ["missed", "skipped"])
            d_delayed = sum(1 for d in day_doses if d.status == "delayed")
            d_upcoming = sum(1 for d in day_doses if d.status in ["pending", "upcoming"])

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
