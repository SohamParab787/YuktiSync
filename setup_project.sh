#!/bin/bash
# Run this FROM INSIDE your repo folder (e.g. YuktiSync/)
# Usage: bash setup_project.sh
# This builds the structure directly here — no extra nested folder.

set -e

echo "Creating full project structure in current directory ($(pwd)) ..."

# =========================================
# ROOT FILES
# =========================================
touch README.md
touch .env.example
touch .gitignore
touch requirements.txt

cat > .gitignore << 'EOF'
__pycache__/
*.pyc
.env
venv/
node_modules/
.DS_Store
*.log
EOF

cat > .env.example << 'EOF'
MONGO_URI=your_mongo_connection_string
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
SECRET_KEY=your_jwt_secret
EOF

cat > requirements.txt << 'EOF'
fastapi
uvicorn[standard]
pydantic
motor
python-dotenv
python-multipart
pytesseract
Pillow
openai
requests
EOF

# =========================================
# BACKEND
# =========================================
mkdir -p backend
cd backend
touch main.py config.py __init__.py

# ---- modules/prescription (PERSON 1) ----
mkdir -p modules/prescription
cd modules/prescription
touch __init__.py ocr_service.py parser_service.py simplifier_service.py explainer_service.py schemas.py routes.py
cd ../..

# ---- modules/schedule (PERSON 2) ----
mkdir -p modules/schedule
cd modules/schedule
touch __init__.py generator_service.py reminder_service.py adherence_service.py escalation_service.py schemas.py routes.py
cd ../..

# ---- modules/risk (PERSON 3) ----
mkdir -p modules/risk
cd modules/risk
touch __init__.py interaction_service.py anti_stacking_service.py severity_util.py schemas.py routes.py
cd ../..

# ---- modules/caregiver (PERSON 4) ----
mkdir -p modules/caregiver
cd modules/caregiver
touch __init__.py invite_service.py dashboard_service.py chat_assistant_service.py schemas.py routes.py
cd ../..

touch modules/__init__.py

# ---- shared ----
mkdir -p shared/models
touch shared/__init__.py shared/database.py shared/ai_client.py
touch shared/models/__init__.py shared/models/user.py shared/models/medication.py shared/models/dose_log.py shared/models/caregiver.py

# ---- tests ----
mkdir -p tests
touch tests/__init__.py tests/test_prescription.py tests/test_schedule.py tests/test_risk.py tests/test_caregiver.py

cd ..  # back to repo root

# =========================================
# FRONTEND
# =========================================
mkdir -p frontend/src/components/prescription
mkdir -p frontend/src/components/schedule
mkdir -p frontend/src/components/risk
mkdir -p frontend/src/components/caregiver
mkdir -p frontend/src/pages
mkdir -p frontend/src/context
mkdir -p frontend/src/api
mkdir -p frontend/public

touch frontend/package.json
touch frontend/src/App.jsx
touch frontend/src/index.js
touch frontend/src/api/prescription.js
touch frontend/src/api/schedule.js
touch frontend/src/api/risk.js
touch frontend/src/api/caregiver.js
touch frontend/src/context/AuthContext.jsx
touch frontend/public/index.html
touch frontend/src/pages/Home.jsx
touch frontend/src/pages/Dashboard.jsx

# =========================================
# DOCS
# =========================================
mkdir -p docs
touch docs/data-schema.md
touch docs/api-endpoints.md

echo ""
echo "✅ Full project structure created in $(pwd)"
echo ""
find . -type f -not -path "./.git/*" | sort
