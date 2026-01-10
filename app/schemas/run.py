from pydantic import BaseModel
from typing import List

class RunRequest(BaseModel):
    model_name: str

class RunSummary(BaseModel):
    run_id: str
    model_name: str
    total_tests: int
    correct: int
    incorrect: int
