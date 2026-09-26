# YuktiSync API Endpoints Documentation

## Base URL
`http://localhost:8000/api`

---

## Module: Caregiver Coordination & Conversational Assistant (Person 4)
Base prefix: `/api/caregiver`

### 1. Invitations & Role-Based Access Control

#### `POST /api/caregiver/invite`
Generate a secure, time-limited JWT invitation token to link a caregiver to a patient.
- **Headers**: `Authorization: Bearer <token>` or `X-User-Id: <id>`
- **Request Body**:
  ```json
  {
    "patient_id": "patient-101",
    "caregiver_email": "priya@example.com",
    "caregiver_name": "Priya Patel",
    "permissions": "read_respond", // "read_only" | "read_respond"
    "expires_in_days": 7
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "id": "link-a1b2c3d4",
    "patient_id": "patient-101",
    "caregiver_email": "priya@example.com",
    "caregiver_name": "Priya Patel",
    "patient_name": "Ramesh Patel",
    "permissions": "read_respond",
    "status": "pending",
    "invite_token": "eyJhbGciOi...",
    "invite_url": "/caregiver/invite?token=eyJhbGciOi...",
    "expires_at": "2026-10-03T06:20:00Z",
    "created_at": "2026-09-26T06:20:00Z",
    "updated_at": "2026-09-26T06:20:00Z"
  }
  ```

#### `POST /api/caregiver/invite/accept`
Accept a caregiver invitation token to link caregiver user account.
- **Request Body**:
  ```json
  {
    "invite_token": "eyJhbGciOi...",
    "caregiver_id": "caregiver-201",
    "caregiver_name": "Priya Patel"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "id": "link-a1b2c3d4",
    "patient_id": "patient-101",
    "caregiver_id": "caregiver-201",
    "caregiver_email": "priya@example.com",
    "caregiver_name": "Priya Patel",
    "patient_name": "Ramesh Patel",
    "permissions": "read_respond",
    "status": "accepted",
    "updated_at": "2026-09-26T06:21:00Z"
  }
  ```

#### `DELETE /api/caregiver/invite/{link_id}`
Revoke access for an active or pending caregiver link.
- **Parameters**: `link_id` (Path, str)
- **Response** (`200 OK`):
  ```json
  {
    "message": "Access revoked successfully.",
    "link_id": "link-a1b2c3d4",
    "success": true
  }
  ```

#### `GET /api/caregiver/invite/list/{patient_id}`
List all caregivers linked or invited to a patient.
- **Response** (`200 OK`): Array of `CaregiverPatientLinkResponse`

#### `GET /api/caregiver/patients`
List all patients linked to the authenticated caregiver.
- **Response** (`200 OK`): Array of `CaregiverPatientLinkResponse`

---

### 2. Caregiver Coordination Dashboard

#### `GET /api/caregiver/dashboard/{patient_id}`
Retrieve a consolidated real-time payload containing:
- Real-time adherence rate (%) and statistics (Person 2 integration)
- Recent taken/missed dose logs
- Upcoming scheduled doses
- Missed-dose escalation alerts (Person 2 integration)
- Shared patient-caregiver notes
- Active medications
- Caregiver permission status (`read_only` vs `read_respond`)

- **Parameters**: `patient_id` (Path, str)
- **Response** (`200 OK`):
  ```json
  {
    "patient_id": "patient-101",
    "patient_name": "Ramesh Patel",
    "caregiver_permission": "read_respond",
    "adherence_summary": {
      "adherence_rate": 75.0,
      "total_scheduled": 4,
      "taken_count": 1,
      "missed_count": 1,
      "upcoming_count": 2
    },
    "recent_doses": [
      {
        "id": "dose-1",
        "patient_id": "patient-101",
        "medication_name": "Metformin",
        "dosage": "500mg",
        "scheduled_time": "Today, 08:00 AM",
        "taken_time": "Today, 08:15 AM",
        "status": "taken",
        "notes": "Taken with breakfast"
      }
    ],
    "upcoming_doses": [
      {
        "id": "dose-3",
        "patient_id": "patient-101",
        "medication_name": "Metformin",
        "dosage": "500mg",
        "scheduled_time": "Today, 08:00 PM",
        "status": "upcoming"
      }
    ],
    "alerts": [
      {
        "id": "alert-1",
        "patient_id": "patient-101",
        "medication_name": "Lisinopril",
        "alert_type": "missed_dose",
        "severity": "high",
        "message": "Missed Lisinopril 10mg morning dose by >2 hours.",
        "is_resolved": false,
        "created_at": "2026-09-26T08:00:00Z"
      }
    ],
    "notes": [
      {
        "id": "note-1",
        "patient_id": "patient-101",
        "author_id": "caregiver-201",
        "author_name": "Priya Patel",
        "author_role": "caregiver",
        "content": "Father felt dizzy yesterday after lunch. Monitored BP: 125/82.",
        "created_at": "2026-09-26T07:30:00Z"
      }
    ],
    "active_medications": [...]
  }
  ```

#### `POST /api/caregiver/notes`
Add a shared note between caregiver and patient.
- **Permissions**: Requires `read_respond`. Blocked with `403 Forbidden` if caregiver has `read_only` permission.
- **Request Body**:
  ```json
  {
    "patient_id": "patient-101",
    "content": "Patient reported feeling well after morning medication."
  }
  ```
- **Response** (`201 Created`): `NoteResponse`

#### `GET /api/caregiver/notes/{patient_id}`
Retrieve all shared notes for a patient, ordered latest first.
- **Response** (`200 OK`): Array of `NoteResponse`

#### `GET /api/caregiver/alerts/{patient_id}`
Retrieve active missed-dose alerts and threshold notifications from Person 2's escalation service.
- **Response** (`200 OK`): Array of `AlertItem`

---

### 3. Voice/Chat Grounded Medication Assistant (RAG)

#### `POST /api/caregiver/chat`
*(Note: Can also be addressed as `/api/assistant/chat` for patient-facing queries)*
Natural language Q&A assistant strictly grounded on retrieved patient facts:
- Prescription instructions & explainer (Person 1)
- Current dosage timetable & due doses (Person 2)
- Drug-drug & drug-food interaction checks and severity rating (Person 3)

- **Request Body**:
  ```json
  {
    "patient_id": "patient-101",
    "query": "Can I take this with paracetamol and ibuprofen?"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "query": "Can I take this with paracetamol and ibuprofen?",
    "answer": "⚠️ Caution: Based on your current medication record, an interaction check was performed. NSAIDs like Ibuprofen may reduce the antihypertensive effect of Lisinopril and increase kidney risk...\n\nDisclaimer: This assistant provides informational guidance based on your records, not formal medical diagnosis.",
    "patient_id": "patient-101",
    "sources": [
      {
        "module": "risk_interaction",
        "title": "Drug-Drug & Drug-Food Interaction Analysis",
        "details": { "evaluated": ["Metformin", "Lisinopril", "Ibuprofen"], "severity": "high" },
        "snippet": "[HIGH] Lisinopril, Ibuprofen: NSAIDs like Ibuprofen may reduce the antihypertensive effect..."
      },
      {
        "module": "prescription_explainer",
        "title": "Prescription Explainer & Direction Knowledge",
        "snippet": "Lisinopril: Lowers blood pressure and prevents heart failure..."
      }
    ],
    "severity": "high",
    "requires_escalation": true,
    "timestamp": "2026-09-26T06:25:00Z"
  }
  ```
