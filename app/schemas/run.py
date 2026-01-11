from pydantic import BaseModel
from typing import Optional

class RunRequest(BaseModel):
    model_name: str
    prompt_version_id: Optional[str] = None  # NEW: Optional, defaults to raw prompt if None

class RunSummary(BaseModel):
    run_id: str
    model_name: str
    prompt_version_id: Optional[str]  # NEW
    total_tests: int
    correct: int
    incorrect: int

    class Config:
        from_attributes = True