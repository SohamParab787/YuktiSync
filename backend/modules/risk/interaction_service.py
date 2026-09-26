"""
Risk Interaction Service (PERSON 3 MODULE)
Public interface for drug-drug, drug-food, and duplicate therapy interaction checks.
"""

from typing import List, Dict, Any, Optional


async def check_drug_interactions(
    medications: List[str], 
    patient_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Public Service Function for Person 3:
    Evaluates list of medications for potential drug-drug or drug-food interactions.
    TODO for Person 3: Connect to FDA / RxNorm interaction database and anti-stacking engine.
    """
    normalized_meds = [m.lower().strip() for m in medications]
    interactions: List[Dict[str, Any]] = []

    # Known interaction rules
    has_metformin = any("metformin" in m for m in normalized_meds)
    has_lisinopril = any("lisinopril" in m for m in normalized_meds)
    has_atorvastatin = any("atorvastatin" in m for m in normalized_meds)
    has_paracetamol = any("paracetamol" in m or "acetaminophen" in m for m in normalized_meds)
    has_ibuprofen = any("ibuprofen" in m or "advil" in m for m in normalized_meds)
    has_alcohol = any("alcohol" in m or "wine" in m or "beer" in m for m in normalized_meds)
    has_grapefruit = any("grapefruit" in m for m in normalized_meds)

    # Rule 1: Lisinopril + Ibuprofen (NSAID interaction)
    if has_lisinopril and has_ibuprofen:
        interactions.append({
            "drugs": ["Lisinopril", "Ibuprofen"],
            "type": "drug-drug",
            "severity": "high",
            "summary": "NSAIDs like Ibuprofen may reduce the antihypertensive effect of Lisinopril and increase nephrotoxicity risk.",
            "recommendation": "Avoid concurrent use or monitor kidney function and blood pressure closely.",
        })

    # Rule 2: Atorvastatin + Grapefruit
    if has_atorvastatin and has_grapefruit:
        interactions.append({
            "drugs": ["Atorvastatin", "Grapefruit"],
            "type": "drug-food",
            "severity": "high",
            "summary": "Grapefruit inhibits CYP3A4, significantly elevating blood levels of Atorvastatin and risking rhabdomyolysis.",
            "recommendation": "Avoid consuming grapefruit or grapefruit juice while taking Atorvastatin.",
        })

    # Rule 3: Metformin + Heavy Alcohol
    if has_metformin and has_alcohol:
        interactions.append({
            "drugs": ["Metformin", "Alcohol"],
            "type": "drug-substance",
            "severity": "critical",
            "summary": "Alcohol potentiates the effect of Metformin on lactate metabolism, increasing the risk of lactic acidosis.",
            "recommendation": "Avoid heavy or acute alcohol consumption while taking Metformin.",
        })

    # Rule 4: Paracetamol + Metformin or Lisinopril
    if has_paracetamol and (has_metformin or has_lisinopril or has_atorvastatin):
        interactions.append({
            "drugs": ["Paracetamol", "Routine Regimen"],
            "type": "drug-drug",
            "severity": "low",
            "summary": "Paracetamol is generally compatible with Metformin, Lisinopril, and Atorvastatin at recommended doses (max 4g/day).",
            "recommendation": "Safe under normal dosages; ensure no other medications contain acetaminophen.",
        })

    return interactions
