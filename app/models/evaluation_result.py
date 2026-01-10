import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
from app.db.base import Base

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_run_id = Column(String, ForeignKey("model_runs.id"), nullable=False)
    test_case_id = Column(String, ForeignKey("test_cases.id"), nullable=False)

    model_output = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
