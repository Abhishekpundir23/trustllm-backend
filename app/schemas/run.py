from pydantic import BaseModel
from typing import Optional

class RunRequest(BaseModel):
    model_name: str
    # FIXED: Changed from int to str because PromptVersion uses UUIDs
    prompt_version_id: Optional[str] = None

class RunSummary(BaseModel):
    run_id: str
    model_name: str
    # FIXED: Changed from int to str
    prompt_version_id: Optional[str] = None
    
    total_tests: int
    correct: int
    incorrect: int
    
    # Analytics
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost: float = 0.0