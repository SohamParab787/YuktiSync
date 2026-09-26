import logging
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

from backend.shared.models.dose_log import DoseLog
from backend.shared.models.medication import Medication

logger = logging.getLogger(__name__)


# In-memory database store with dynamic Prescription -> Medication -> Schedule linkage
class InMemoryDB:
    def __init__(self, seed_demo: bool = False):
        self._lock = threading.RLock()
        self.users: Dict[str, Dict[str, Any]] = {}
        self.caregiver_links: Dict[str, Dict[str, Any]] = {}
        self.caregiver_notes: List[Dict[str, Any]] = []
        self.prescriptions: Dict[str, List[Dict[str, Any]]] = {}
        self.medications: Dict[str, List[Any]] = {}
        self.dose_logs: Dict[str, List[Any]] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.caregivers: Dict[str, Dict[str, Any]] = {}
        self.risk_alerts: Dict[str, Dict[str, Any]] = {}
        self.escalation_logs: List[Dict[str, Any]] = []
        self.activity_logs: List[Dict[str, Any]] = []

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

    def save_medication(self, medication: Medication) -> Medication:
        owner_id = medication.user_id or medication.patient_id
        if not owner_id:
            raise ValueError("Medication must have a patient_id or user_id")
        with self._lock:
            medications = self.medications.setdefault(owner_id, [])
            for index, existing in enumerate(medications):
                if getattr(existing, "id", None) == medication.id:
                    medications[index] = medication
                    break
            else:
                medications.append(medication)
        return medication

    def get_medication(self, medication_id: str) -> Optional[Medication]:
        with self._lock:
            return next(
                (medication for medications in self.medications.values()
                 for medication in medications
                 if getattr(medication, "id", None) == medication_id),
                None,
            )

    def get_medications_by_user(self, user_id: str) -> List[Medication]:
        with self._lock:
            return [
                medication for medication in self.medications.get(user_id, [])
                if isinstance(medication, Medication)
            ]

    def save_dose_log(self, dose_log: DoseLog) -> DoseLog:
        owner_id = dose_log.user_id or dose_log.patient_id
        if not owner_id:
            raise ValueError("Dose log must have a patient_id or user_id")
        with self._lock:
            dose_logs = self.dose_logs.setdefault(owner_id, [])
            for index, existing in enumerate(dose_logs):
                if getattr(existing, "id", None) == dose_log.id:
                    dose_logs[index] = dose_log
                    break
            else:
                dose_logs.append(dose_log)
        return dose_log

    def get_dose_log(self, dose_id: str) -> Optional[DoseLog]:
        with self._lock:
            return next(
                (dose for doses in self.dose_logs.values()
                 for dose in doses
                 if getattr(dose, "id", None) == dose_id),
                None,
            )

    def get_dose_logs_by_user(self, user_id: str) -> List[DoseLog]:
        with self._lock:
            dose_logs = self.dose_logs.get(user_id, [])
            for index, dose in enumerate(dose_logs):
                if isinstance(dose, dict):
                    dose_logs[index] = DoseLog(
                        id=str(dose.get("id", f"dose-{uuid.uuid4().hex[:8]}")),
                        patient_id=dose.get("patient_id", user_id),
                        medication_id=dose.get("medication_id"),
                        medication_name=dose.get("medication_name", "Medication"),
                        dosage=dose.get("dosage", "1 dose"),
                        user_id=dose.get("user_id", user_id),
                        scheduled_time=str(dose.get("scheduled_time", "")),
                        status=dose.get("status", "upcoming"),
                        taken_time=dose.get("taken_time"),
                        taken_at=dose.get("taken_at"),
                        food_instruction=dose.get("food_instruction"),
                        notes=dose.get("notes"),
                        instructions=dose.get("instructions"),
                        grace_period_minutes=dose.get("grace_period_minutes", 60),
                        created_at=dose.get("created_at", datetime.now(timezone.utc)),
                    )
            return [dose for dose in dose_logs if isinstance(dose, DoseLog)]

    def get_all_dose_logs(self) -> List[DoseLog]:
        with self._lock:
            user_ids = list(self.dose_logs)
        return [dose for user_id in user_ids for dose in self.get_dose_logs_by_user(user_id)]

    def update_dose_log(self, dose_log: DoseLog) -> DoseLog:
        self.save_dose_log(dose_log)
        return dose_log

    def record_activity(
        self,
        user_id: str,
        dose_id: str,
        medication_name: str,
        action: str,
        details: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            activity = {
                "id": f"act-{uuid.uuid4().hex[:8]}",
                "user_id": user_id,
                "dose_id": dose_id,
                "medication_name": medication_name,
                "action": action,
                "details": details,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.activity_logs.insert(0, activity)
            return activity

    def get_activities(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            return [item for item in self.activity_logs if item.get("user_id") == user_id][:limit]

    def record_escalation(self, event: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self.escalation_logs.insert(0, event)
            severity = {
                "INFO": "medium",
                "WARNING": "high",
                "CRITICAL": "critical",
            }.get(str(event.get("alert_level", "")).upper(), "medium")
            self.alerts.insert(0, {
                "id": event.get("id", f"alert-{uuid.uuid4().hex[:8]}"),
                "patient_id": event.get("user_id"),
                "medication_name": ", ".join(event.get("medications", [])) or "Prescription",
                "alert_type": "missed_dose",
                "severity": severity,
                "message": event.get("message", "Medication schedule escalation"),
                "scheduled_time": event.get("timestamp"),
                "is_resolved": False,
                "created_at": event.get("timestamp", datetime.now(timezone.utc)),
            })
            return event

    def get_escalations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            return [event for event in self.escalation_logs if event.get("user_id") == user_id][:limit]

    def clear(self):
        with self._lock:
            self.users.clear()
            self.caregiver_links.clear()
            self.caregiver_notes.clear()
            self.prescriptions.clear()
            self.medications.clear()
            self.dose_logs.clear()
            self.alerts.clear()
            self.caregivers.clear()
            self.risk_alerts.clear()
            self.escalation_logs.clear()
            self.activity_logs.clear()

    def update_dose_status(self, patient_id: str, dose_id: str, new_status: str) -> Optional[Any]:
        """Log dose as taken or missed, updating adherence and alerts in real-time"""
        logs = self.dose_logs.get(patient_id, [])
        for log in logs:
            if getattr(log, "id", None) == dose_id or (isinstance(log, dict) and log.get("id") == dose_id):
                if isinstance(log, DoseLog):
                    log.status = new_status
                    if new_status == "taken":
                        log.taken_time = datetime.now(timezone.utc).strftime("%I:%M %p")
                    elif new_status == "missed":
                        log.taken_time = None
                    if new_status == "taken":
                        self.alerts = [
                            alert for alert in self.alerts
                            if not (
                                alert.get("patient_id") == patient_id
                                and alert.get("medication_name") == log.medication_name
                            )
                        ]
                    elif new_status == "missed":
                        self.alerts.append({
                            "id": f"alert-{uuid.uuid4().hex[:6]}",
                            "patient_id": patient_id,
                            "medication_name": log.medication_name,
                            "alert_type": "missed_dose",
                            "severity": "high",
                            "message": f"Escalation Alert: Missed scheduled dose of {log.medication_name} ({log.dosage}).",
                            "scheduled_time": datetime.now(timezone.utc),
                            "is_resolved": False,
                            "created_at": datetime.now(timezone.utc),
                        })
                    return log
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


def get_db() -> InMemoryDB:
    """Dependency or accessor for shared DB instance"""
    return db
