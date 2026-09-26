"""
Prescription Explainer Service (PERSON 1 MODULE)
Public interface for medicine explanations, directions, and precautions.
"""

from typing import Optional, Dict, Any


async def get_medicine_explanation(medication_name: str, patient_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Public Service Function for Person 1:
    Fetches patient-friendly explanation, instructions, precautions, and food advice for a medicine.
    TODO for Person 1: Connect to full OCR/prescription parsing database and LLM explainer pipeline.
    """
    name_clean = medication_name.strip().title()
    
    # Standard medical reference mock/stub knowledge
    med_knowledge = {
        "Metformin": {
            "name": "Metformin",
            "purpose": "Controls blood sugar in Type 2 Diabetes by reducing glucose production in the liver.",
            "instructions": "Take with breakfast or dinner to minimize gastrointestinal discomfort.",
            "precautions": "Avoid heavy alcohol consumption. Stay well-hydrated.",
            "common_side_effects": ["Mild nausea", "Stomach upset", "Diarrhea"],
            "food_interactions": "Take with meals.",
        },
        "Lisinopril": {
            "name": "Lisinopril",
            "purpose": "Lowers blood pressure and prevents heart failure by relaxing blood vessels.",
            "instructions": "Take in the morning with or without food. Drink plenty of water.",
            "precautions": "Monitor blood pressure regularly. Avoid potassium supplements unless advised.",
            "common_side_effects": ["Dry cough", "Dizziness upon standing"],
            "food_interactions": "Avoid excessive potassium-rich salt substitutes.",
        },
        "Atorvastatin": {
            "name": "Atorvastatin",
            "purpose": "Lowers LDL cholesterol and cardiovascular risk.",
            "instructions": "Take once daily in the evening or bedtime.",
            "precautions": "Avoid grapefruit and grapefruit juice as it increases drug concentration.",
            "common_side_effects": ["Mild muscle aches", "Joint pain"],
            "food_interactions": "Grapefruit / grapefruit juice interacts negatively.",
        },
        "Paracetamol": {
            "name": "Paracetamol (Acetaminophen)",
            "purpose": "Pain relief and fever reduction.",
            "instructions": "Do not exceed 4,000 mg in 24 hours to prevent liver toxicity.",
            "precautions": "Do not combine with other medications containing acetaminophen.",
            "common_side_effects": ["Rare if taken within prescribed dose limit"],
            "food_interactions": "Avoid excessive alcohol.",
        },
    }

    if name_clean in med_knowledge:
        return med_knowledge[name_clean]

    return {
        "name": medication_name,
        "purpose": f"Prescribed medication ({medication_name}) for patient therapy.",
        "instructions": "Take strictly as prescribed on your bottle label.",
        "precautions": "Contact your doctor if unexpected symptoms occur.",
        "common_side_effects": ["Check packaging insert for details"],
        "food_interactions": "Follow doctor's instructions regarding food.",
    }
