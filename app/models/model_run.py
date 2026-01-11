from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db.base import Base

class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # FIXED: Changed from UUID to Integer to match your Project IDs
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    model_name = Column(String, nullable=False)
    status = Column(String, default="pending")

    # Optional: Link to prompt version if you are using Phase 2 code
    prompt_version_id = Column(String, ForeignKey("prompt_versions.id"), nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)