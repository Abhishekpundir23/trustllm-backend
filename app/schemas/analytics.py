from pydantic import BaseModel
from typing import List

class FailingTest(BaseModel):
    test_id: int
    prompt: str
    failure_count: int

class HealthResponse(BaseModel):
    pass_rate: float        # Current success % (0-100)
    drift: float            # Change from previous run (e.g. -5.2%)
    models_compared: int    # Count of unique models used
    regression_score: float # A calculated score of performance drop
    worst_failing_tests: List[FailingTest]