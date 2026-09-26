from pydantic import BaseModel, Field
from typing import Optional

class User(BaseModel):
    id: str
    name: str
    email: str
    caregiver_id: Optional[str] = None
