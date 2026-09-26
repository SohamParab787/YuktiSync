"""
Schedule Adherence Service (PERSON 2 MODULE)

Tracks medication dose adherence, missed doses, delayed doses,
anti-stacking safety checks, and adherence analytics.
"""

from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

from backend.shared.models.dose_log import DoseLog
from backend.shared.database import get_db


class AdherenceService:
    """
    Adherence Service for YuktiSync.

    Handles:
    - Dose status tracking
    - Automatic missed-dose detection
    - Daily adherence
    - Weekly adherence
    - Anti-stacking safety checks
    - Dose activity logging
    """

    def __init__(self, db=None):
        self.db = db or get_db()

    def auto_transition_missed_doses(
        self,
        user_id: Optional[str] = None,
        grace_period_minutes: int = 60
    ) -> List[DoseLog]:
        """
        Automatically marks pending/upcoming doses as missed
        after the configured grace period.
        """
        now = datetime.now()
        transitioned = []

        all_doses = (
            self.db.get_dose_logs_by_user(user_id)
            if user_id
            else self.db.get_all_dose_logs()
        )

        for dose in all_doses:
            if dose.status in ["pending", "upcoming"]:
                try:
                    sched_dt = datetime.fromisoformat(dose.scheduled_time)
                    grace_minutes = (
                        dose.grace_period_minutes
                        or grace_period_minutes
                    )
                    grace = timedelta(minutes=grace_minutes)

                    if now > sched_dt + grace:
                        dose.status = "missed"
                        self.db.update_dose_log(dose)

                        self.db.record_activity(
                            user_id=dose.user_id,
                            dose_id=dose.id,
                            medication_name=dose.medication_name,
                            action="Auto-marked as Missed",
                            details=(
                                f"Dose was unconfirmed after "
                                f"{grace_minutes} min grace window."
                            )
                        )

                        transitioned.append(dose)

                except (ValueError, TypeError):
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
        Updates the status of a medication dose.

        Supported statuses:
        taken, missed, delayed, skipped, pending, upcoming
        """

        dose = self.db.get_dose_log(dose_id)

        if not dose:
            raise ValueError(f"Dose with ID '{dose_id}' not found.")

        target_status = status.lower()

        allowed_statuses = [
            "taken",
            "missed",
            "delayed",
            "skipped",
            "pending",
            "upcoming"
        ]

        if target_status not in allowed_statuses:
            raise ValueError(
                f"Invalid status '{status}'. "
                "Must be taken, missed, delayed, skipped, pending, or upcoming."
            )

        taken_timestamp = taken_at or datetime.now().isoformat()

        # If taken after the grace period, mark it as delayed.
        if target_status == "taken":
            try:
                sched_dt = datetime.fromisoformat(dose.scheduled_time)
                actual_dt = datetime.fromisoformat(taken_timestamp)

                grace = timedelta(
                    minutes=dose.grace_period_minutes
                )

                if actual_dt > sched_dt + grace:
                    target_status = "delayed"

            except (ValueError, TypeError):
                pass

        dose.status = target_status

        if target_status in ["taken", "delayed"]:
            dose.taken_at = taken_timestamp

        if notes:
            dose.notes = notes

        updated = self.db.update_dose_log(dose)

        action_map = {
            "taken": "Marked as Taken",
            "delayed": "Marked as Delayed",
            "missed": "Marked as Missed",
            "skipped": "Marked as Skipped",
            "pending": "Reset to Pending",
            "upcoming": "Marked as Upcoming"
        }

        self.db.record_activity(
            user_id=dose.user_id,
            dose_id=dose.id,
            medication_name=dose.medication_name,
            action=action_map.get(
                target_status,
                f"Status updated to {target_status}"
            ),
            details=(
                f"Dosage: {dose.dosage} | "
                f"Scheduled: {dose.scheduled_time} | "
                f"Notes: {notes or 'None'}"
            )
        )

        return updated

    def evaluate_anti_stacking(
        self,
        user_id: str,
        dose_id: Optional[str] = None,
        medication_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Checks whether taking a missed dose could conflict
        with the next scheduled dose.

        This function provides a safety recommendation only.
        It does not change the prescribed dosage automatically.
        """

        all_doses = self.db.get_dose_logs_by_user(user_id)
        target_med = medication_name

        if dose_id:
            current_dose = self.db.get_dose_log(dose_id)

            if current_dose:
                target_med = current_dose.medication_name

        if not target_med and all_doses:
            target_med = all_doses[0].medication_name

        disclaimer = (
            "Medication decisions should follow prescribed instructions "
            "or professional guidance. Never automatically change "
            "your prescribed dosage."
        )

        if not target_med:
            return {
                "status": "SAFE TO TAKE",
                "recommendation": (
                    "No scheduled doses found to conflict with."
                ),
                "hours_until_next_dose": None,
                "next_scheduled_time": None,
                "stacking_risk_detected": False,
                "disclaimer": disclaimer
            }

        now = datetime.now()
        future_doses = []
        missed_count = 0

        for dose in all_doses:

            if dose.medication_name.lower() == target_med.lower():

                if dose.status in ["missed", "skipped"]:
                    missed_count += 1

                try:
                    scheduled_dt = datetime.fromisoformat(
                        dose.scheduled_time
                    )

                    if (
                        scheduled_dt > now
                        and dose.status in ["pending", "upcoming"]
                    ):
                        future_doses.append(
                            (scheduled_dt, dose)
                        )

                except (ValueError, TypeError):
                    pass

        future_doses.sort(key=lambda item: item[0])

        if missed_count >= 2:
            next_time = (
                future_doses[0][1].scheduled_time
                if future_doses
                else None
            )

            hours_until = (
                (future_doses[0][0] - now).total_seconds() / 3600.0
                if future_doses
                else None
            )

            return {
                "status": "CONSULT PROFESSIONAL",
                "recommendation": (
                    f"You have missed {missed_count} doses of "
                    f"{target_med}. Please consult your physician "
                    "or pharmacist before resuming this medication."
                ),
                "hours_until_next_dose": hours_until,
                "next_scheduled_time": next_time,
                "stacking_risk_detected": True,
                "disclaimer": disclaimer
            }

        if not future_doses:
            return {
                "status": "SAFE TO TAKE",
                "recommendation": (
                    f"No immediate next dose scheduled for "
                    f"{target_med}. Follow your prescribed instructions."
                ),
                "hours_until_next_dose": None,
                "next_scheduled_time": None,
                "stacking_risk_detected": False,
                "disclaimer": disclaimer
            }

        next_dt, next_dose = future_doses[0]

        hours_diff = (
            next_dt - now
        ).total_seconds() / 3600.0

        time_formatted = next_dt.strftime("%I:%M %p")

        # Safety threshold for potential dose stacking.
        if hours_diff < 4.0:
            return {
                "status": "WAIT / SKIP",
                "recommendation": (
                    f"Your next scheduled dose of {target_med} "
                    f"is only {hours_diff:.1f} hours away at "
                    f"{time_formatted}. Do not double-dose. "
                    "Follow your prescribed missed-dose instructions "
                    "or consult a healthcare professional."
                ),
                "hours_until_next_dose": round(hours_diff, 1),
                "next_scheduled_time": next_dose.scheduled_time,
                "stacking_risk_detected": True,
                "disclaimer": disclaimer
            }

        return {
            "status": "SAFE TO TAKE",
            "recommendation": (
                f"Your next scheduled dose of {target_med} is "
                f"{hours_diff:.1f} hours away at {time_formatted}. "
                "Follow your prescribed dosage."
            ),
            "hours_until_next_dose": round(hours_diff, 1),
            "next_scheduled_time": next_dose.scheduled_time,
            "stacking_risk_detected": False,
            "disclaimer": disclaimer
        }

    def get_daily_adherence(
        self,
        user_id: str,
        target_date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """Computes adherence metrics for a specific day."""

        self.auto_transition_missed_doses(user_id=user_id)

        target_date = target_date_str or date.today().isoformat()

        user_doses = self.db.get_dose_logs_by_user(user_id)

        todays_doses = [
            dose
            for dose in user_doses
            if dose.scheduled_time.startswith(target_date)
        ]

        total = len(todays_doses)

        taken = sum(
            1 for dose in todays_doses
            if dose.status == "taken"
        )

        missed = sum(
            1 for dose in todays_doses
            if dose.status in ["missed", "skipped"]
        )

        delayed = sum(
            1 for dose in todays_doses
            if dose.status == "delayed"
        )

        upcoming = sum(
            1 for dose in todays_doses
            if dose.status in ["pending", "upcoming"]
        )

        due_total = taken + missed + delayed

        if due_total > 0:
            percentage = round(
                ((taken + (0.5 * delayed)) / due_total) * 100,
                1
            )
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

    def get_weekly_adherence(
        self,
        user_id: str,
        start_date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """Computes adherence metrics for a 7-day window."""

        self.auto_transition_missed_doses(user_id=user_id)

        start_d = (
            datetime.strptime(
                start_date_str,
                "%Y-%m-%d"
            ).date()
            if start_date_str
            else date.today() - timedelta(days=6)
        )

        end_d = start_d + timedelta(days=6)

        user_doses = self.db.get_dose_logs_by_user(user_id)

        daily_breakdown = []

        total_taken = 0
        total_missed = 0
        total_delayed = 0
        total_upcoming = 0

        for day_offset in range(7):

            current_date = (
                start_d + timedelta(days=day_offset)
            )

            current_date_str = current_date.isoformat()

            day_doses = [
                dose
                for dose in user_doses
                if dose.scheduled_time.startswith(
                    current_date_str
                )
            ]

            day_total = len(day_doses)

            day_taken = sum(
                1 for dose in day_doses
                if dose.status == "taken"
            )

            day_missed = sum(
                1 for dose in day_doses
                if dose.status in ["missed", "skipped"]
            )

            day_delayed = sum(
                1 for dose in day_doses
                if dose.status == "delayed"
            )

            day_upcoming = sum(
                1 for dose in day_doses
                if dose.status in ["pending", "upcoming"]
            )

            day_due = day_taken + day_missed + day_delayed

            day_percentage = (
                round(
                    (
                        (day_taken + (0.5 * day_delayed))
                        / day_due
                    ) * 100,
                    1
                )
                if day_due > 0
                else 100.0
            )

            total_taken += day_taken
            total_missed += day_missed
            total_delayed += day_delayed
            total_upcoming += day_upcoming

            daily_breakdown.append({
                "date": current_date_str,
                "total_doses": day_total,
                "taken_doses": day_taken,
                "missed_doses": day_missed,
                "delayed_doses": day_delayed,
                "upcoming_doses": day_upcoming,
                "adherence_percentage": day_percentage,
                "doses": [
                    dose.model_dump()
                    for dose in day_doses
                ]
            })

        overall_due = (
            total_taken
            + total_missed
            + total_delayed
        )

        overall_percentage = (
            round(
                (
                    (total_taken + (0.5 * total_delayed))
                    / overall_due
                ) * 100,
                1
            )
            if overall_due > 0
            else 100.0
        )

        return {
            "user_id": user_id,
            "view_type": "weekly",
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "total_doses": (
                total_taken
                + total_missed
                + total_delayed
                + total_upcoming
            ),
            "taken_doses": total_taken,
            "missed_doses": total_missed,
            "delayed_doses": total_delayed,
            "upcoming_doses": total_upcoming,
            "overall_adherence_percentage": overall_percentage,
            "daily_breakdown": daily_breakdown
        }


async def get_adherence_summary(
    patient_id: str
) -> Dict[str, Any]:
    """
    Backward-compatible public function.

    Keeps compatibility with existing Schedule/Caregiver code
    that expects get_adherence_summary().
    """

    service = AdherenceService()

    daily = service.get_daily_adherence(patient_id)

    logs = service.db.get_dose_logs_by_user(patient_id)

    return {
        "patient_id": patient_id,
        "adherence_rate": daily["adherence_percentage"],
        "total_scheduled": daily["total_doses"],
        "taken_count": daily["taken_doses"],
        "missed_count": daily["missed_doses"],
        "upcoming_count": daily["upcoming_doses"],
        "recent_doses": [
            dose.model_dump()
            for dose in logs
        ]
    }