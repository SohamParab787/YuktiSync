"""
Feature 7: Adaptive Missed-Dose Rescheduling Engine ("Anti-Stacking").

When a user logs a dose as taken late, this decides whether it's safe to
take it now, whether the next dose should be delayed to avoid two doses
being active in the body too close together ("stacking"), or whether the
missed dose should be skipped entirely to avoid overdose/toxicity risk.

NOTE: The half-life data below is illustrative for demo purposes only,
not clinical guidance. In a real product this logic would be reviewed by
a pharmacist/clinician and backed by a real pharmacokinetic dataset.

Heuristic used (simplified, conservative):
  - Let interval = normal hours between doses (e.g. 8h for a TID drug).
  - Let late_ratio = hours_late / interval.
  - late_ratio < 0.5   -> safe to take now, no change to next dose.
  - 0.5 <= late_ratio < 0.75 -> take now, but delay the next dose to
        preserve safe spacing (avoid overlapping peak concentrations).
  - late_ratio >= 0.75 -> too close to the next dose: skip this one
        entirely to avoid double-dosing / stacking risk.
  - Drugs with a "narrow therapeutic index" (flagged below) are treated
    more conservatively (thresholds tightened) since even small stacking
    can be dangerous for them.
"""

from datetime import datetime, timedelta
from .schemas import MissedDoseRequest, MissedDoseResponse, MissedDoseAction, SeverityLevel


# Drugs where overlapping doses is especially risky (narrow therapeutic index).
# Swap this for real clinical flags in production.
NARROW_THERAPEUTIC_INDEX_DRUGS = {
    "warfarin",
    "digoxin",
    "levothyroxine",
    "lithium",
    "phenytoin",
}


def _get_interval_hours(request: MissedDoseRequest) -> float:
    if request.dosing_interval_hours:
        return request.dosing_interval_hours
    delta = request.next_scheduled_time - request.scheduled_time
    hours = delta.total_seconds() / 3600
    return hours if hours > 0 else 8.0  # sane fallback


def evaluate_missed_dose(request: MissedDoseRequest) -> MissedDoseResponse:
    drug = request.drug_name.strip().lower()
    interval = _get_interval_hours(request)

    hours_late = (request.current_time - request.scheduled_time).total_seconds() / 3600
    hours_late = max(hours_late, 0.0)

    is_narrow_index = drug in NARROW_THERAPEUTIC_INDEX_DRUGS

    # Tighten thresholds for narrow-therapeutic-index drugs
    safe_threshold = 0.4 if is_narrow_index else 0.5
    delay_threshold = 0.6 if is_narrow_index else 0.75

    late_ratio = hours_late / interval if interval > 0 else 1.0

    if late_ratio < safe_threshold:
        action = MissedDoseAction.TAKE_NOW
        severity = SeverityLevel.INFO
        message = "It's safe to take this dose now."
        reasoning = (
            f"You are {hours_late:.1f}h late, which is well within a safe window "
            f"before your next scheduled dose ({interval:.1f}h apart). Taking it now "
            f"will not cause meaningful overlap with your next dose."
        )
        adjusted_next = request.next_scheduled_time

    elif late_ratio < delay_threshold:
        action = MissedDoseAction.TAKE_NOW_DELAY_NEXT
        severity = SeverityLevel.WARNING
        # Push the next dose out by the amount of time this one was late,
        # capped so it doesn't push into the following day's schedule oddly.
        delay_hours = min(hours_late, interval * 0.5)
        adjusted_next = request.next_scheduled_time + timedelta(hours=delay_hours)
        message = (
            f"Safe to take now, but your next dose will be delayed by "
            f"about {delay_hours:.1f} hour(s)."
        )
        reasoning = (
            f"You are {hours_late:.1f}h late — taking it now is fine, but to avoid "
            f"two doses being active in your system too close together, your next "
            f"dose has been shifted from {request.next_scheduled_time.strftime('%H:%M')} "
            f"to {adjusted_next.strftime('%H:%M')}."
        )

    else:
        action = MissedDoseAction.SKIP_DOSE
        severity = SeverityLevel.CRITICAL if is_narrow_index else SeverityLevel.WARNING
        message = "Skip this dose. Do not take it now — wait for your next scheduled dose."
        reasoning = (
            f"You are {hours_late:.1f}h late, which is too close to your next scheduled "
            f"dose ({interval:.1f}h apart). Taking it now risks two doses overlapping in "
            f"your system, which can lead to excess medication levels. Skip this dose and "
            f"resume your normal schedule at the next scheduled time."
        )
        adjusted_next = request.next_scheduled_time

    if is_narrow_index and action != MissedDoseAction.TAKE_NOW:
        # For narrow-therapeutic-index drugs, always nudge the user to double check.
        reasoning += (
            " This medication has a narrow safety margin, so if you're unsure, "
            "confirm with your doctor or pharmacist before proceeding."
        )

    return MissedDoseResponse(
        action=action,
        severity=severity,
        message=message,
        reasoning=reasoning,
        adjusted_next_dose_time=adjusted_next,
        hours_late=round(hours_late, 2),
    )
