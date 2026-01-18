from pydantic import BaseModel
from typing import Optional, Dict

class TestCaseCreate(BaseModel):
    prompt: str
    task_type: str  # math | logic | instruction | safety | rag
    # 👇 NEW: Context for RAG tests
    context: Optional[str] = None 
    rules: Optional[Dict] = None
    expected: Optional[str] = None

class TestCaseResponse(BaseModel):
    id: int
    prompt: str
    task_type: str
    # 👇 NEW: Return context to frontend
    context: Optional[str] = None
    rules: Optional[Dict]
    expected: Optional[str]

    class Config:
        from_attributes = True