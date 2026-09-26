import uuid
import httpx
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from backend.shared.models.medication import Medication
from backend.shared.models.dose_log import DoseLog
from backend.shared.database import get_db

class GeneratorService:
    def __init__(self, db=None):
        self.db = db or get_db()

    @staticmethod
    def parse_scheduled_times(frequency: str, times_provided: Optional[List[str]] = None) -> List[str]:
        if times_provided and isinstance(times_provided, list) and len(times_provided) > 0:
            return times_provided

        freq_lower = (frequency or "").lower()
        if "twice" in freq_lower or "2 times" in freq_lower or "bid" in freq_lower or "every 12" in freq_lower:
            return ["08:00", "20:00"]
        elif "three" in freq_lower or "3 times" in freq_lower or "tid" in freq_lower or "every 8" in freq_lower:
            return ["08:00", "14:00", "20:00"]
        elif "four" in freq_lower or "4 times" in freq_lower or "qid" in freq_lower or "every 6" in freq_lower:
            return ["08:00", "12:00", "16:00", "20:00"]
        else: # Default once daily
            return ["09:00"]

    async def fetch_prescription_from_api(self, user_id: str, prescription_id: Optional[str] = None, base_url: str = "http://localhost:8000") -> List[Dict[str, Any]]:
        """
        Consumes prescription data from Person 1's module via /api/prescription/* endpoint.
        """
        url = f"{base_url}/api/prescription/{prescription_id}" if prescription_id else f"{base_url}/api/prescription/user/{user_id}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        return data.get("medications", [data])
        except Exception:
            pass
        return []

    async def generate_schedule(
        self,
        user_id: str,
        prescription_id: Optional[str] = None,
        prescription_data: Optional[Dict[str, Any]] = None,
        start_date_str: Optional[str] = None,
        duration_days: Optional[int] = None,
        base_url: str = "http://localhost:8000"
    ) -> Dict[str, Any]:
        """
        Builds timetable from prescription data and saves to DB.
        """
        meds_raw = []
        if prescription_data:
            if isinstance(prescription_data.get("medications"), list):
                meds_raw = prescription_data["medications"]
            elif "name" in prescription_data or "medication_name" in prescription_data:
                meds_raw = [prescription_data]
        
        if not meds_raw and (prescription_id or user_id):
            meds_raw = await self.fetch_prescription_from_api(user_id, prescription_id, base_url)

        # Fallback default if no prescription data is available via API or payload
        if not meds_raw:
            meds_raw = [
                {
                    "name": "Amoxicillin",
                    "dosage": "500mg",
                    "frequency": "twice daily",
                    "duration_days": 7,
                    "instructions": "Take after meals"
                },
                {
                    "name": "Lisinopril",
                    "dosage": "10mg",
                    "frequency": "once daily",
                    "duration_days": 30,
                    "instructions": "Take in the morning"
                }
            ]

        start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else date.today()

        created_med_ids = []
        created_doses_count = 0

        existing_doses = self.db.get_dose_logs_by_user(user_id)
        existing_dose_times = {d.scheduled_time + "_" + d.medication_name.lower() for d in existing_doses}

        for item in meds_raw:
            med_name = item.get("name") or item.get("medication_name") or "Unnamed Medication"
            dosage = item.get("dosage", "1 dose")
            frequency = item.get("frequency", "once daily")
            item_duration = duration_days or item.get("duration_days") or item.get("duration") or 7
            instructions = item.get("instructions") or item.get("notes") or ""
            scheduled_times = self.parse_scheduled_times(frequency, item.get("scheduled_times"))

            end_d = start_d + timedelta(days=item_duration - 1)
            med_id = f"med-{uuid.uuid4().hex[:8]}"

            medication_model = Medication(
                id=med_id,
                user_id=user_id,
                prescription_id=prescription_id or item.get("prescription_id"),
                name=med_name,
                dosage=dosage,
                frequency=frequency,
                times_per_day=len(scheduled_times),
                scheduled_times=scheduled_times,
                duration_days=item_duration,
                start_date=start_d.isoformat(),
                end_date=end_d.isoformat(),
                instructions=instructions,
                active=True
            )
            self.db.save_medication(medication_model)
            created_med_ids.append(med_id)

            # Generate daily doses
            curr_date = start_d
            while curr_date <= end_d:
                for time_str in scheduled_times:
                    scheduled_iso = f"{curr_date.isoformat()}T{time_str}:00"
                    dedup_key = f"{scheduled_iso}_{med_name.lower()}"

                    if dedup_key not in existing_dose_times:
                        dose_id = f"dose-{uuid.uuid4().hex[:8]}"
                        dose_log = DoseLog(
                            id=dose_id,
                            medication_id=med_id,
                            medication_name=med_name,
                            dosage=dosage,
                            user_id=user_id,
                            scheduled_time=scheduled_iso,
                            status="upcoming",
                            instructions=instructions,
                            grace_period_minutes=60
                        )
                        self.db.save_dose_log(dose_log)
                        existing_dose_times.add(dedup_key)
                        created_doses_count += 1
                curr_date += timedelta(days=1)

        return {
            "message": "Schedule successfully generated",
            "medications_created": len(created_med_ids),
            "doses_created": created_doses_count,
            "medication_ids": created_med_ids
        }
