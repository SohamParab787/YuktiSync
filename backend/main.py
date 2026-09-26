"""
YuktiSync - Main FastAPI entrypoint.

RULES FOR THE TEAM (read before editing this file):
1. Each person only ADDS their own import line + include_router line.
2. NEVER delete or reorder someone else's two lines.
3. NEVER edit code inside someone else's module folder from here.
4. Pull the latest main.py before adding your lines, to avoid conflicts.

This file just WIRES modules together. All real logic lives inside
each person's own modules/<name>/ folder.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config  # loads .env — must run before any module that needs env vars

app = FastAPI(
title="YuktiSync API",
description="AI-powered medication management & adherence platform",
version="1.0.0",
)

# Allow the frontend (running on a different port) to call this API.
# For a hackathon, allow_origins=["*"] is fine. Tighten before any real deployment.
app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)


# ============================================================
# ROUTER REGISTRATION
# Each person adds exactly 2 lines here: one import, one include.
# Keep them in this same order (1, 2, 3, 4) so diffs stay clean.
# ============================================================

# ---- Person 1: Prescription module ----
# from modules.prescription.routes import router as prescription_router
# app.include_router(prescription_router, prefix="/api/prescription", tags=["prescription"])

# ---- Person 2: Schedule module ----
# from modules.schedule.routes import router as schedule_router
# app.include_router(schedule_router, prefix="/api/schedule", tags=["schedule"])

# ---- Person 3: Risk module ----
from modules.risk.routes import router as risk_router
app.include_router(risk_router, prefix="/api/risk", tags=["risk"])

# ---- Person 4: Caregiver module ----
# from modules.caregiver.routes import router as caregiver_router
# app.include_router(caregiver_router, prefix="/api/caregiver", tags=["caregiver"])


# ============================================================
# ROOT / HEALTH CHECK — leave this as-is, everyone can use it
# to confirm the server is up.
# ============================================================

@app.get("/")
async def root():
    return {
        "message": "Yukit Sync API is running",
        "docs": "/docs",
        "modules": ["prescription", "schedule", "risk", "caregiver"],
        }


@app.get("/health")
async def health_check():
    return {"status": "ok"}