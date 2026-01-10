from pydantic import BaseModel
from typing import Optional, Dict

class TestCaseCreate(BaseModel):
    prompt: str
    task_type: str  # math | logic | instruction | safety
    rules: Optional[Dict] = None
    expected: Optional[str] = None

class TestCaseResponse(BaseModel):
    id: str
    prompt: str
    task_type: str
    rules: Optional[Dict]
    expected: Optional[str]

    class Config:
        from_attributes = True
