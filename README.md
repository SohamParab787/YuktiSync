YuktiSync — Risk Module

AI-powered medication safety checks for the YuktiSync platform.

This module implements two core features:

Interaction & Allergy Checker (Feature 4)

Adaptive Missed-Dose / Anti-Stacking Engine (Feature 7)

Overview

YuktiSync is an AI-powered medication management and adherence platform.
The Risk module focuses on real-time safety:

Detecting dangerous drug–drug, drug–allergy, and drug–food interactions

Giving clear, actionable guidance when a patient takes a dose late (to avoid dangerous “stacking”)

Disclaimer: This is a hackathon prototype.
Interaction checks use an LLM (not a licensed clinical database).
Missed-dose logic uses simplified pharmacokinetic heuristics.
Not medical advice. Always consult a pharmacist or doctor.

Features

1. Interaction Checker (POST /api/risk/check-interactions)

Takes a patient’s medication list (plus optional allergies and food items) and returns:

Drug–drug interactions

Allergy conflicts

Food / lifestyle warnings

Each result is tagged with a severity level:

Severity

Meaning

CRITICAL

Potentially dangerous – seek professional advice

WARNING

Caution needed

INFO

Mild / informational

Powered by gpt-4o-mini via a structured JSON prompt.

2. Missed-Dose / Anti-Stacking Engine (POST /api/risk/missed-dose-decision)

When a user logs a dose late, the engine decides one of:

Action

When it triggers

TAKE_NOW

Late but still safely within the dosing window

TAKE_NOW_DELAY_NEXT

Take now, but push the next dose to avoid overlap

SKIP_DOSE

Too close to the next dose – skip to avoid stacking

CONSULT_DOCTOR

Reserved for edge cases

Heuristic (simplified):

late_ratio = hours_late / dosing_interval

late_ratio < 0.5 → TAKE_NOW
0.5 – 0.75 → TAKE_NOW_DELAY_NEXT
≥ 0.75 → SKIP_DOSE

Narrow-therapeutic-index drugs (Warfarin, Digoxin, Lithium, Phenytoin, Levothyroxine) use tighter thresholds and stronger warnings.

API Endpoints

Base path: /api/risk

Method

Endpoint

Description

GET

/health

Module health check

POST

/check-interactions

Run interaction / allergy / food check

POST

/missed-dose-decision

Get guidance for a late dose

Example: Interaction Check

curl -X POST http://127.0.0.1:8000/api/risk/check-interactions \
 -H "Content-Type: application/json" \
 -d '{
"medications": ["Warfarin", "Ibuprofen"],
"allergies": ["Penicillin"],
"food_items": ["Grapefruit"]
}'

Example: Missed-Dose Decision

curl -X POST http://127.0.0.1:8000/api/risk/missed-dose-decision \
 -H "Content-Type: application/json" \
 -d '{
"drug_name": "Metformin",
"scheduled_time": "2026-09-26T08:00:00",
"current_time": "2026-09-26T13:00:00",
"next_scheduled_time": "2026-09-26T20:00:00"
}'

Full request/response schemas live in backend/modules/risk/schemas.py.

Project Structure (Risk Module)

backend/modules/risk/
├── **init**.py
├── routes.py # FastAPI router
├── schemas.py # Pydantic models
├── interaction_service.py # Feature 4 – LLM interaction checker
├── anti_stacking_service.py # Feature 7 – missed-dose engine
└── severity_util.py # Shared severity helpers + badge styles

frontend/src/
├── api/risk.js # Thin API client
└── components/risk/
├── RiskPanel.jsx # Tabbed container
├── InteractionChecker.jsx
├── MissedDoseChecker.jsx
├── SeverityBadge.jsx
└── RiskPanel.css

The router is registered in backend/main.py:

from modules.risk.routes import router as risk_router
app.include_router(risk_router, prefix="/api/risk", tags=["risk"])

Setup & Run

Backend

# From project root

python -m venv venv
source venv/bin/activate # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Required env vars (in .env)

OPENAI_API_KEY=sk-...

# Run

cd backend
uvicorn main:app --reload --port 8000

Interactive docs: http://127.0.0.1:8000/docs

Frontend (Risk UI)

cd frontend
npm install
npm run dev

Drop the component anywhere:

import RiskPanel from "./components/risk/RiskPanel";

<RiskPanel />

Dependencies (relevant)

fastapi + uvicorn

pydantic

openai (for interaction checks)

python-dotenv

Notes for Team / Judges

Interaction logic is intentionally LLM-based so it can reason about uncommon combinations without a huge static DB.

Anti-stacking logic is conservative and specially tightened for narrow-therapeutic-index drugs.

Both features return plain-English explanations suitable for patients.

Severity levels and badge styles are shared so the UI stays consistent.

Future Improvements

Replace / augment LLM checks with a real clinical source (RxNorm, DrugBank, FDB, etc.)

Add pharmacokinetic half-life data instead of pure interval heuristics

Persist check history per patient

Push critical alerts to the Caregiver module

Module owner: VISHRUTH (Innov8r123) (Risk)
Platform: YuktiSync – AI-powered medication management & adherence
