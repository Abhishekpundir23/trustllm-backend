import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
# Note: We removed the UUID import since we don't need it for the foreign key anymore
from app.db.base import Base

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # FIXED: Changed from UUID to Integer to match ModelRun.id
    model_run_id = Column(Integer, ForeignKey("model_runs.id"), nullable=False)
    
    test_case_id = Column(Integer, ForeignKey("tests.id"), nullable=False)

    model_output = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    category = Column(String, nullable=False)