from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    PATIENT = "patient"
    CAREGIVER = "caregiver"
    DOCTOR = "doctor"


class User(BaseModel):
    id: str = Field(..., description="Unique identifier for the user")
    email: str = Field(..., description="User's email address")
    name: str = Field(..., description="User's full name")
    role: UserRole = Field(default=UserRole.PATIENT, description="User role in the system")
    caregiver_id: Optional[str] = None
    phone_number: Optional[str] = Field(default=None, description="Optional contact number")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
