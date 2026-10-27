# YuktiSync — Risk Module

AI-powered medication safety checks for the YuktiSync platform.

This module implements two core features:

1. **Interaction & Allergy Checker** (Feature 4)
2. **Adaptive Missed-Dose / Anti-Stacking Engine** (Feature 7)

---

## Overview

YuktiSync is an AI-powered medication management and adherence platform.  
The **Risk module** focuses on real-time safety:

- Detecting dangerous drug–drug, drug–allergy, and drug–food interactions
- Giving clear, actionable guidance when a patient takes a dose late (to avoid dangerous “stacking”)

> **Disclaimer**: This is a hackathon prototype.  
> Interaction checks use an LLM (not a licensed clinical database).  
> Missed-dose logic uses simplified pharmacokinetic heuristics.  
> **Not medical advice.** Always consult a pharmacist or doctor.

---

## Features

### 1. Interaction Checker (`POST /api/risk/check-interactions`)

Takes a patient’s medication list (plus optional allergies and food items) and returns:

- Drug–drug interactions
- Allergy conflicts
- Food / lifestyle warnings

Each result is tagged with a severity level:

| Severity   | Meaning                                          |
| ---------- | ------------------------------------------------ |
| `CRITICAL` | Potentially dangerous – seek professional advice |
| `WARNING`  | Caution needed                                   |
| `INFO`     | Mild / informational                             |

Powered by `gpt-4o-mini` via a structured JSON prompt.

### 2. Missed-Dose / Anti-Stacking Engine (`POST /api/risk/missed-dose-decision`)

When a user logs a dose late, the engine decides one of:

| Action                | When it triggers                                    |
| --------------------- | --------------------------------------------------- |
| `TAKE_NOW`            | Late but still safely within the dosing window      |
| `TAKE_NOW_DELAY_NEXT` | Take now, but push the next dose to avoid overlap   |
| `SKIP_DOSE`           | Too close to the next dose – skip to avoid stacking |
| `CONSULT_DOCTOR`      | Reserved for edge cases                             |

**Heuristic** (simplified):

```text
late_ratio = hours_late / dosing_interval

late_ratio < 0.5   → TAKE_NOW
0.5 – 0.75         → TAKE_NOW_DELAY_NEXT
≥ 0.75             → SKIP_DOSE

Narrow-therapeutic-index drugs (Warfarin, Digoxin, Lithium, Phenytoin, Levothyroxine) use tighter thresholds and stronger warnings.

## Overview
textbackend/modules/risk/
├── __init__.py
├── routes.py                 # FastAPI router
├── schemas.py                # Pydantic models
├── interaction_service.py    # Feature 4 – LLM interaction checker
├── anti_stacking_service.py  # Feature 7 – missed-dose engine
└── severity_util.py          # Shared severity helpers + badge styles

frontend/src/
├── api/risk.js                       # Thin API client
└── components/risk/
    ├── RiskPanel.jsx                 # Tabbed container
    ├── InteractionChecker.jsx
    ├── MissedDoseChecker.jsx
    ├── SeverityBadge.jsx
    └── RiskPanel.css
```
