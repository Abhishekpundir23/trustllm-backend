import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # FIXED: Type UUID to match ModelRun.id
    model_run_id = Column(UUID(as_uuid=True), ForeignKey("model_runs.id"), nullable=False)
    
    # FIXED: Type Integer to match TestCase.id
    test_case_id = Column(Integer, ForeignKey("tests.id"), nullable=False)

    model_output = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    category = Column(String, nullable=False)