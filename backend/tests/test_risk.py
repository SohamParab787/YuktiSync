"""
Basic tests for the Risk module. Run with:
    pytest tests/test_risk.py -v

These also double as usage examples for Person 4 (who will call this
module from the chat assistant and caregiver dashboard).
"""

from datetime import datetime, timedelta
from modules.risk.schemas import InteractionCheckRequest, MissedDoseRequest
from modules.risk.interaction_service import check_interactions
from modules.risk.anti_stacking_service import evaluate_missed_dose


def test_critical_drug_drug_interaction_detected():
    req = InteractionCheckRequest(medications=["Warfarin", "Ibuprofen"])
    result = check_interactions(req)
    assert result.has_critical is True
    assert len(result.drug_interactions) == 1
    assert result.drug_interactions[0].severity == "CRITICAL"


def test_no_interactions_found():
    req = InteractionCheckRequest(medications=["Paracetamol"])
    result = check_interactions(req)
    assert result.has_critical is False
    assert len(result.drug_interactions) == 0


def test_food_interaction_detected():
    req = InteractionCheckRequest(
        medications=["Atorvastatin"],
        food_items=["Grapefruit"],
    )
    result = check_interactions(req)
    assert len(result.food_warnings) == 1
    assert result.food_warnings[0].food_item == "Grapefruit"


def test_allergy_conflict_detected():
    req = InteractionCheckRequest(
        medications=["Amoxicillin"],
        allergies=["Penicillin"],
    )
    result = check_interactions(req)
    assert len(result.allergy_warnings) == 1
    assert result.has_critical is True


def test_missed_dose_safe_to_take_now():
    scheduled = datetime(2026, 9, 26, 8, 0)
    current = datetime(2026, 9, 26, 9, 0)  # 1 hour late
    next_dose = datetime(2026, 9, 26, 16, 0)  # 8-hour interval
    req = MissedDoseRequest(
        drug_name="Metformin",
        scheduled_time=scheduled,
        current_time=current,
        next_scheduled_time=next_dose,
    )
    result = evaluate_missed_dose(req)
    assert result.action == "TAKE_NOW"


def test_missed_dose_skip_when_too_close_to_next():
    scheduled = datetime(2026, 9, 26, 8, 0)
    current = datetime(2026, 9, 26, 15, 0)  # 7 hours late
    next_dose = datetime(2026, 9, 26, 16, 0)  # only 1 hour away now
    req = MissedDoseRequest(
        drug_name="Metformin",
        scheduled_time=scheduled,
        current_time=current,
        next_scheduled_time=next_dose,
    )
    result = evaluate_missed_dose(req)
    assert result.action == "SKIP_DOSE"


def test_missed_dose_narrow_index_drug_more_conservative():
    scheduled = datetime(2026, 9, 26, 8, 0)
    current = datetime(2026, 9, 26, 11, 0)  # 3 hours late
    next_dose = datetime(2026, 9, 26, 16, 0)  # 8-hour interval, ratio = 0.375
    req = MissedDoseRequest(
        drug_name="Warfarin",  # narrow therapeutic index
        scheduled_time=scheduled,
        current_time=current,
        next_scheduled_time=next_dose,
    )
    result = evaluate_missed_dose(req)
    # 0.375 < 0.4 safe threshold for narrow-index drugs, so still safe here
    assert result.action == "TAKE_NOW"
