"""
FastAPI routes for the Risk module (Person 3).

Mounted in main.py as:
    app.include_router(risk_router, prefix="/api/risk", tags=["risk"])

Endpoints:
    POST /api/risk/check-interactions   -> Feature 4
    POST /api/risk/missed-dose-decision -> Feature 7
    GET  /api/risk/health               -> simple health check
"""

from fastapi import APIRouter, HTTPException

from .schemas import (
    InteractionCheckRequest,
    InteractionCheckResponse,
    MissedDoseRequest,
    MissedDoseResponse,
)
from .interaction_service import check_interactions
from .anti_stacking_service import evaluate_missed_dose

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "module": "risk"}


@router.post("/check-interactions", response_model=InteractionCheckResponse)
async def check_interactions_endpoint(payload: InteractionCheckRequest):
    """
    Feature 4: checks a patient's medication list for drug-drug,
    drug-food, and allergy conflicts. Returns severity-tiered warnings.
    """
    if not payload.medications:
        raise HTTPException(status_code=400, detail="At least one medication is required.")
    try:
        return check_interactions(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interaction check failed: {str(e)}")


@router.post("/missed-dose-decision", response_model=MissedDoseResponse)
async def missed_dose_decision_endpoint(payload: MissedDoseRequest):
    """
    Feature 7: Anti-Stacking Engine. Given a late-logged dose, decides
    whether it's safe to take now, should be delayed, or skipped.
    """
    if payload.current_time < payload.scheduled_time:
        raise HTTPException(
            status_code=400,
            detail="current_time cannot be before scheduled_time.",
        )
    try:
        return evaluate_missed_dose(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Missed-dose evaluation failed: {str(e)}")
