from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db.base import Base

class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    model_name = Column(String, nullable=False)
    status = Column(String, default="pending")

    # FIXED: Changed Integer to String because Prompt IDs are UUIDs
    prompt_version_id = Column(String, ForeignKey("prompt_versions.id"), nullable=True)

    # Analytics
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)