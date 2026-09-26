from pydantic import BaseModel, Field
from typing import Optional

class Caregiver(BaseModel):
    id: str
    user_id: str
    name: str
    phone: Optional[str] = None
    email: str
    status: str = "active"
