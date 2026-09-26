"""
Feature 4: Drug Interaction & Risk Checker (AI-powered).

Uses the shared OpenAI client to reason about drug-drug, drug-food, and
allergy conflicts instead of a hardcoded lookup table.

NOTE: This is still not a licensed clinical data source. For a real
product, model output like this should be paired with (or verified
against) a real drug-interaction database (RxNav/NLM, DrugBank, FDB).
Treat this as a smart first-pass check, not medical advice.
"""

import json
from typing import List

from backend.shared.ai_client import ai_client
from .schemas import (
    InteractionCheckRequest,
    InteractionCheckResponse,
    InteractionResult,
    AllergyWarning,
    FoodWarning,
    SeverityLevel,
)
from .severity_util import highest_severity

MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You are a clinical safety assistant checking a patient's
medication list for drug-drug interactions, drug-food/lifestyle conflicts,
and allergy conflicts.

Respond with ONLY a JSON object (no markdown, no prose) in exactly this shape:

{
  "drug_interactions": [
    {"drug_a": "...", "drug_b": "...", "severity": "CRITICAL|WARNING|INFO", "hazard": "...", "explanation": "..."}
  ],
  "allergy_warnings": [
    {"medication": "...", "allergen": "...", "severity": "CRITICAL|WARNING|INFO", "explanation": "..."}
  ],
  "food_warnings": [
    {"medication": "...", "food_item": "...", "severity": "CRITICAL|WARNING|INFO", "explanation": "..."}
  ]
}

Rules:
- Only include entries for conflicts that actually exist. Empty arrays are fine and expected when nothing conflicts.
- severity must be exactly one of CRITICAL, WARNING, INFO.
- explanation should be a short, plain-English sentence a patient can understand.
- Use the medication/food/allergen names as given by the user (title-cased is fine).
- Do not include any text outside the JSON object.
"""


def _normalize(items: List[str]) -> List[str]:
    return [i.strip() for i in items if i and i.strip()]


def _build_user_prompt(meds: List[str], allergies: List[str], foods: List[str]) -> str:
    return (
        f"Medications: {', '.join(meds) if meds else 'none'}\n"
        f"Allergies: {', '.join(allergies) if allergies else 'none'}\n"
        f"Food/lifestyle items: {', '.join(foods) if foods else 'none'}"
    )


def _safe_severity(value: str) -> SeverityLevel:
    try:
        return SeverityLevel(value.upper())
    except Exception:
        return SeverityLevel.INFO


async def check_interactions(request: InteractionCheckRequest) -> InteractionCheckResponse:
    meds = _normalize(request.medications)
    allergies = _normalize(request.allergies or [])
    foods = _normalize(request.food_items or [])

    drug_interactions: List[InteractionResult] = []
    allergy_warnings: List[AllergyWarning] = []
    food_warnings: List[FoodWarning] = []

    try:
        response = await ai_client.generate_chat_response(
            messages=[{"role": "user", "content": _build_user_prompt(meds, allergies, foods)}],
            system_prompt=SYSTEM_PROMPT,
            temperature=0,
            max_tokens=600,
        )
        parsed = json.loads(response)

        for item in parsed.get("drug_interactions", []):
            drug_interactions.append(
                InteractionResult(
                    drug_a=item.get("drug_a", "").title(),
                    drug_b=item.get("drug_b", "").title(),
                    severity=_safe_severity(item.get("severity", "INFO")),
                    hazard=item.get("hazard", ""),
                    explanation=item.get("explanation", ""),
                )
            )

        for item in parsed.get("allergy_warnings", []):
            allergy_warnings.append(
                AllergyWarning(
                    medication=item.get("medication", "").title(),
                    allergen=item.get("allergen", "").title(),
                    severity=_safe_severity(item.get("severity", "CRITICAL")),
                    explanation=item.get("explanation", ""),
                )
            )

        for item in parsed.get("food_warnings", []):
            food_warnings.append(
                FoodWarning(
                    medication=item.get("medication", "").title(),
                    food_item=item.get("food_item", "").title(),
                    severity=_safe_severity(item.get("severity", "WARNING")),
                    explanation=item.get("explanation", ""),
                )
            )

        model_failed = False

    except Exception as e:
        print("OpenAI call failed:", repr(e))
        model_failed = True

    all_severities = (
        [r.severity for r in drug_interactions]
        + [r.severity for r in allergy_warnings]
        + [r.severity for r in food_warnings]
    )
    overall = highest_severity(all_severities) if all_severities else SeverityLevel.INFO
    has_critical = overall == SeverityLevel.CRITICAL

    if model_failed:
        summary = (
            "We couldn't complete an automated check right now. "
            "Please consult a pharmacist or doctor about this combination."
        )
    elif not all_severities:
        summary = "No known interactions found among the listed medications, allergies, or foods."
    elif has_critical:
        summary = "⚠️ CRITICAL interaction(s) found. Please consult a doctor or pharmacist before proceeding."
    else:
        summary = "Some interactions found that need caution. Review the warnings below."

    return InteractionCheckResponse(
        has_critical=has_critical,
        drug_interactions=drug_interactions,
        allergy_warnings=allergy_warnings,
        food_warnings=food_warnings,
        summary=summary,
    )


async def check_drug_interactions(medications: List[str], patient_id: str = "") -> List[dict]:
    """Compatibility adapter for the caregiver assistant's interaction contract."""
    result = await check_interactions(InteractionCheckRequest(medications=_normalize(medications)))
    interactions = [
        {
            "severity": item.severity.value.lower(),
            "drugs": [item.drug_a, item.drug_b],
            "summary": item.explanation,
            "recommendation": item.hazard,
        }
        for item in result.drug_interactions
    ]
    interactions.extend(
        {
            "severity": item.severity.value.lower(),
            "drugs": [item.medication, item.allergen],
            "summary": item.explanation,
            "recommendation": "Consult a clinician about this allergy.",
        }
        for item in result.allergy_warnings
    )
    interactions.extend(
        {
            "severity": item.severity.value.lower(),
            "drugs": [item.medication, item.food_item],
            "summary": item.explanation,
            "recommendation": "Follow the prescription and ask a clinician if unsure.",
        }
        for item in result.food_warnings
    )
    return interactions
