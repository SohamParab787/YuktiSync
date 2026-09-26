import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from backend.shared.database import db
from backend.shared.ai_client import ai_client
from backend.modules.caregiver.schemas import ChatResponse, SourceItem

# Person 1 Integrations
from backend.modules.prescription.explainer_service import get_medicine_explanation

# Person 2 Integrations
from backend.modules.schedule.adherence_service import get_adherence_summary
from backend.modules.schedule.generator_service import get_upcoming_doses

# Person 3 Integrations
from backend.modules.risk.interaction_service import check_drug_interactions
from backend.modules.risk.severity_util import classify_severity

logger = logging.getLogger(__name__)


def extract_potential_meds_from_query(query: str) -> List[str]:
    """Extract candidate medication names mentioned in freeform text"""
    common_meds = [
        "paracetamol", "acetaminophen", "ibuprofen", "advil", "aspirin",
        "metformin", "lisinopril", "atorvastatin", "amlodipine", "omeprazole",
        "grapefruit", "alcohol", "wine", "beer", "tylenol", "naproxen"
    ]
    query_lower = query.lower()
    found = [m.title() for m in common_meds if m in query_lower]
    return found


async def answer_medication_query(
    patient_id: str,
    query: str,
    user_context: Optional[Dict[str, Any]] = None,
) -> ChatResponse:
    """
    RAG-grounded Conversational Medication Assistant:
    1. Grounding Retrieval from Person 1 (Prescription Explainer), Person 2 (Schedule Timetable),
       and Person 3 (Risk Interaction & Severity Engine).
    2. Enforces risk module check if drug/food combinations are mentioned.
    3. Synthesizes response strictly grounded on retrieved facts via shared ai_client.
    4. Handles timeouts/failures gracefully without compromising patient safety.
    """
    sources: List[SourceItem] = []
    overall_severity = "none"
    requires_escalation = False

    # 1. Retrieve Active Patient Medications
    active_meds = db.medications.get(patient_id, [])
    active_med_names = [m.get("name") for m in active_meds if m.get("name")]
    if not active_med_names:
        active_med_names = ["Metformin", "Lisinopril", "Atorvastatin"]

    # 2. Schedule Grounding (Person 2)
    schedule_context_str = ""
    try:
        adherence_data = await get_adherence_summary(patient_id)
        upcoming_data = await get_upcoming_doses(patient_id)
        
        recent_logs = adherence_data.get("recent_doses", [])
        schedule_snippets = []
        for log in recent_logs:
            schedule_snippets.append(
                f"- {log.get('medication_name')} {log.get('dosage')}: {log.get('status').upper()} ({log.get('scheduled_time')})"
            )
        
        schedule_context_str = "\n".join(schedule_snippets)
        sources.append(
            SourceItem(
                module="schedule_service",
                title="Current Medication Schedule & Adherence Logs",
                details={
                    "adherence_rate": adherence_data.get("adherence_rate"),
                    "missed_count": adherence_data.get("missed_count"),
                },
                snippet=f"Adherence Rate: {adherence_data.get('adherence_rate')}%. Recent items:\n{schedule_context_str}",
            )
        )
    except Exception as e:
        logger.error(f"Schedule retrieval failed: {e}")
        schedule_context_str = "Schedule data temporarily unavailable."

    # 3. Explainer Grounding (Person 1)
    explainer_context_str = ""
    try:
        # Fetch explanation for active meds or meds mentioned in query
        mentioned_meds = extract_potential_meds_from_query(query)
        all_meds_to_explain = list(set(active_med_names + mentioned_meds))
        
        explainer_snippets = []
        for med_name in all_meds_to_explain[:4]:  # limit to top 4 relevant
            info = await get_medicine_explanation(med_name, patient_id=patient_id)
            explainer_snippets.append(
                f"- {info.get('name')}: {info.get('purpose')}. Instructions: {info.get('instructions')}. Precautions: {info.get('precautions')}"
            )
        
        explainer_context_str = "\n".join(explainer_snippets)
        sources.append(
            SourceItem(
                module="prescription_explainer",
                title="Prescription Explainer & Direction Knowledge",
                details={"medications_referenced": all_meds_to_explain[:4]},
                snippet=explainer_context_str,
            )
        )
    except Exception as e:
        logger.error(f"Explainer retrieval failed: {e}")
        explainer_context_str = "Medicine information lookup unavailable."

    # 4. Risk & Interaction Check (Person 3)
    query_implies_risk = any(
        kw in query.lower()
        for kw in [
            "take with", "together", "interaction", "paracetamol", "ibuprofen",
            "aspirin", "alcohol", "grapefruit", "side effect", "risk", "can i take", "safe"
        ]
    )

    risk_context_str = "No specific drug interactions flagged."
    if query_implies_risk:
        try:
            extra_substances = extract_potential_meds_from_query(query)
            eval_meds = list(set(active_med_names + extra_substances))
            
            interactions = await check_drug_interactions(eval_meds, patient_id=patient_id)
            overall_severity = classify_severity(interactions)
            
            if interactions:
                risk_snippets = []
                for inter in interactions:
                    risk_snippets.append(
                        f"[{inter.get('severity', 'low').upper()}] {', '.join(inter.get('drugs', []))}: {inter.get('summary')} (Recommendation: {inter.get('recommendation')})"
                    )
                risk_context_str = "\n".join(risk_snippets)
                if overall_severity in ["high", "critical"]:
                    requires_escalation = True
            else:
                risk_context_str = "No known contraindications found for evaluated medications."

            sources.append(
                SourceItem(
                    module="risk_interaction",
                    title="Drug-Drug & Drug-Food Interaction Analysis",
                    details={"evaluated": eval_meds, "severity": overall_severity},
                    snippet=f"Overall Severity: {overall_severity.upper()}.\n{risk_context_str}",
                )
            )
        except Exception as e:
            logger.error(f"Risk module interaction check failed: {e}")
            overall_severity = "medium"
            risk_context_str = (
                "⚠️ Notice: Interaction verification engine is currently running in offline fallback mode. "
                "Consult a pharmacist or physician before combining medications."
            )

    # 5. Formulate Grounded LLM Prompt
    system_prompt = f"""You are YuktiSync's Clinical Grounded Medication Assistant.
Your task is to answer medication questions accurately, empathetically, and safely for patients and caregivers.

STRICT CLINICAL SAFETY DIRECTIVES:
1. Ground your answer EXCLUSIVELY on the retrieved facts below. Do NOT use unverified assumptions or generic medical knowledge.
2. If the user asks about taking medications together or about interactions, rely STRICTLY on the Risk & Interaction section.
3. If risk severity is HIGH or CRITICAL, clearly highlight the potential danger and advise contacting the doctor or pharmacist immediately.
4. If asked 'What do I take now?' or regarding schedule, refer directly to the Schedule & Adherence Logs.
5. Always provide an explicit, responsible safety disclaimer at the end.

=== CLINICAL GROUNDING DATA ===
[Schedule & Adherence Logs]
{schedule_context_str}

[Prescription Explainer & Instructions]
{explainer_context_str}

[Risk & Interaction Checks]
Severity: {overall_severity.upper()}
{risk_context_str}
================================
"""

    messages = [
        {"role": "user", "content": query}
    ]

    try:
        raw_answer = await ai_client.generate_chat_response(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.2,
        )
    except Exception as e:
        logger.error(f"AI response generation error: {e}")
        # Safe fallback degradation
        if overall_severity in ["high", "critical"]:
            raw_answer = (
                f"⚠️ Caution: Based on the interaction safety check, an interaction was identified: {risk_context_str}. "
                "Please do not combine these without explicit confirmation from your physician or pharmacist.\n\n"
                "Disclaimer: This assistant provides informational support and does not replace certified medical consultation."
            )
        else:
            raw_answer = (
                "I have retrieved your schedule and prescription details from your YuktiSync records. "
                "Please follow your prescription schedule carefully. If you have any unusual symptoms, contact your doctor.\n\n"
                "Disclaimer: This guidance is based on on-file records only."
            )

    return ChatResponse(
        query=query,
        answer=raw_answer,
        patient_id=patient_id,
        sources=sources,
        severity=overall_severity,
        requires_escalation=requires_escalation,
        timestamp=datetime.now(timezone.utc),
    )
