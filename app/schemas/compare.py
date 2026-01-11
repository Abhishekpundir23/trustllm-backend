from pydantic import BaseModel
from typing import List, Optional

class ComparisonRow(BaseModel):
    test_id: int
    prompt: str
    expected: Optional[str]
    
    # Run 1 Data
    run1_output: Optional[str]
    run1_score: Optional[int]
    
    # Run 2 Data
    run2_output: Optional[str]
    run2_score: Optional[int]

class ComparisonResponse(BaseModel):
    project_id: int
    run1_id: str
    run1_name: str
    run2_id: str
    run2_name: str
    
    comparisons: List[ComparisonRow]