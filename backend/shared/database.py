import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)


# In-memory database store with dynamic Prescription -> Medication -> Schedule linkage
class InMemoryDB:
    def __init__(self, seed_demo: bool = False):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.caregiver_links: Dict[str, Dict[str, Any]] = {}
        self.caregiver_notes: List[Dict[str, Any]] = []
        self.prescriptions: Dict[str, List[Dict[str, Any]]] = {}
        self.medications: Dict[str, List[Dict[str, Any]]] = {}
        self.dose_logs: Dict[str, List[Dict[str, Any]]] = {}
        self.alerts: List[Dict[str, Any]] = []

        if seed_demo:
            self.seed_demo_data()

    def seed_demo_data(self):
        """Seed demo data for unit testing (not used in clean live mode)"""
        # Default Patient & Caregiver
        self.users["patient-101"] = {
            "id": "patient-101",
            "name": "Ramesh Patel",
            "email": "ramesh@example.com",
            "role": "patient",
        }
        self.users["caregiver-201"] = {
            "id": "caregiver-201",
            "name": "Priya Patel",
            "email": "priya@example.com",
            "role": "caregiver",
        }

        # Active link
        link_id = "link-001"
        self.caregiver_links[link_id] = {
            "id": link_id,
            "patient_id": "patient-101",
            "caregiver_id": "caregiver-201",
            "caregiver_email": "priya@example.com",
            "caregiver_name": "Priya Patel",
            "patient_name": "Ramesh Patel",
            "permissions": "read_respond",
            "status": "accepted",
            "invite_token": None,
            "expires_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        # Prescription 1 (Dr. Anita Sengupta — Max Healthcare)
        initial_prescription = {
            "id": "rx-84920",
            "patient_id": "patient-101",
            "patient_name": "Ramesh Patel",
            "rx_number": "RX-84920-IND",
            "doctor_name": "Dr. Anita Sengupta, MD (Cardiology & Diabetology)",
            "clinic_name": "Max Healthcare Multispeciality Clinic",
            "issued_date": "2026-09-24",
            "diagnosis": "Type 2 Diabetes Mellitus & Stage 1 Essential Hypertension",
            "instructions": "Monitor fasting blood glucose and morning BP daily. Review in 4 weeks.",
            "medications": [
                {
                    "id": "med-1",
                    "patient_id": "patient-101",
                    "name": "Metformin XR",
                    "dosage": "500mg",
                    "frequency": "Twice daily after meals",
                    "timing_slots": ["08:00 AM", "08:00 PM"],
                    "instructions": "Take with breakfast and dinner",
                    "prescribed_by": "Dr. Anita Sengupta",
                    "duration": "90 Days",
                    "refills": 3,
                    "warnings": ["Take with food to prevent GI upset"],
                },
                {
                    "id": "med-2",
                    "patient_id": "patient-101",
                    "name": "Lisinopril",
                    "dosage": "10mg",
                    "frequency": "Once daily morning",
                    "timing_slots": ["09:00 AM"],
                    "instructions": "Take in morning with water",
                    "prescribed_by": "Dr. Anita Sengupta",
                    "duration": "90 Days",
                    "refills": 3,
                    "warnings": ["Monitor blood pressure regularly"],
                },
                {
                    "id": "med-3",
                    "patient_id": "patient-101",
                    "name": "Atorvastatin",
                    "dosage": "20mg",
                    "frequency": "Once daily at bedtime",
                    "timing_slots": ["10:00 PM"],
                    "instructions": "Take at night before sleep",
                    "prescribed_by": "Dr. Anita Sengupta",
                    "duration": "90 Days",
                    "refills": 2,
                    "warnings": ["Avoid grapefruit juice"],
                },
            ],
        }

        self.apply_prescription("patient-101", initial_prescription, seed_logs=True)

        # Caregiver shared notes
        self.caregiver_notes = [
            {
                "id": "note-1",
                "patient_id": "patient-101",
                "author_id": "caregiver-201",
                "author_name": "Priya Patel",
                "author_role": "caregiver",
                "content": "Patient vitals monitored: BP 124/80, fasting glucose 110 mg/dL. Regimen active.",
                "created_at": datetime.now(timezone.utc),
            },
            {
                "id": "note-2",
                "patient_id": "patient-101",
                "author_id": "patient-101",
                "author_name": "Ramesh Patel",
                "author_role": "patient",
                "content": "Completed morning medication with breakfast on time.",
                "created_at": datetime.now(timezone.utc),
            }
        ]

    def apply_prescription(self, patient_id: str, prescription: Dict[str, Any], seed_logs: bool = False):
        """
        Derive active medications, daily timetable slots, and escalation alerts
        directly from a clinical prescription object.
        """
        if patient_id not in self.prescriptions:
            self.prescriptions[patient_id] = []
        
        # Add to prescription archive
        self.prescriptions[patient_id].append(prescription)

        # Store patient name if provided
        patient_name = prescription.get("patient_name")
        if patient_name:
            self.users[patient_id] = {
                "id": patient_id,
                "name": patient_name,
                "role": "patient"
            }

        # Extract prescribed medications
        meds = prescription.get("medications", [])
        self.medications[patient_id] = meds

        # Generate schedule dose logs directly from prescription timing slots
        dose_logs = []
        alerts = []
        dose_counter = 1

        for med in meds:
            timing_slots = med.get("timing_slots", ["09:00 AM"])
            for slot in timing_slots:
                status = "upcoming"
                taken_time = None
                notes = med.get("instructions", "")

                if seed_logs:
                    if "08:00 AM" in slot:
                        status = "taken"
                        taken_time = "Today, 08:15 AM"
                        notes = "Logged taken with morning meal"
                    elif "09:00 AM" in slot:
                        status = "missed"
                        taken_time = None
                        notes = f"Missed morning dose of {med.get('name')}"
                        alerts.append({
                            "id": f"alert-{dose_counter}",
                            "patient_id": patient_id,
                            "medication_name": med.get("name"),
                            "alert_type": "missed_dose",
                            "severity": "high",
                            "message": f"Prescription Alert: Missed {med.get('name')} {med.get('dosage')} scheduled for {slot} by >2 hours.",
                            "scheduled_time": datetime.now(timezone.utc),
                            "is_resolved": False,
                            "created_at": datetime.now(timezone.utc),
                        })

                dose_logs.append({
                    "id": f"dose-{dose_counter}",
                    "patient_id": patient_id,
                    "medication_name": med.get("name"),
                    "dosage": med.get("dosage"),
                    "scheduled_time": f"Today, {slot}",
                    "taken_time": taken_time,
                    "status": status,
                    "notes": notes,
                    "prescribed_by": med.get("prescribed_by", prescription.get("doctor_name")),
                    "rx_number": prescription.get("rx_number"),
                })
                dose_counter += 1

        self.dose_logs[patient_id] = dose_logs
        if alerts:
            self.alerts.extend(alerts)

    def update_dose_status(self, patient_id: str, dose_id: str, new_status: str) -> Optional[Dict[str, Any]]:
        """Log dose as taken or missed, updating adherence and alerts in real-time"""
        logs = self.dose_logs.get(patient_id, [])
        for log in logs:
            if log.get("id") == dose_id:
                log["status"] = new_status
                if new_status == "taken":
                    log["taken_time"] = datetime.now(timezone.utc).strftime("%I:%M %p")
                    # Clear any active alert for this medication
                    self.alerts = [
                        a for a in self.alerts
                        if not (a.get("patient_id") == patient_id and a.get("medication_name") == log.get("medication_name"))
                    ]
                elif new_status == "missed":
                    log["taken_time"] = None
                    self.alerts.append({
                        "id": f"alert-{uuid.uuid4().hex[:6]}",
                        "patient_id": patient_id,
                        "medication_name": log.get("medication_name"),
                        "alert_type": "missed_dose",
                        "severity": "high",
                        "message": f"Escalation Alert: Missed scheduled dose of {log.get('medication_name')} ({log.get('dosage')}).",
                        "scheduled_time": datetime.now(timezone.utc),
                        "is_resolved": False,
                        "created_at": datetime.now(timezone.utc),
                    })
                return log
        return None

    def clear_patient(self, patient_id: str):
        """Wipe clean patient prescriptions, medications, dose logs, and notes"""
        self.prescriptions.pop(patient_id, None)
        self.medications.pop(patient_id, None)
        self.dose_logs.pop(patient_id, None)
        self.users.pop(patient_id, None)
        self.alerts = [a for a in self.alerts if a.get("patient_id") != patient_id]
        self.caregiver_notes = [n for n in self.caregiver_notes if n.get("patient_id") != patient_id]


db = InMemoryDB(seed_demo=False)


def get_db():
    """Dependency or accessor for shared DB instance"""
    return db
