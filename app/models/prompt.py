import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from app.db.base import Base

class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    version = Column(Integer, nullable=False)
    template = Column(Text, nullable=False)  # The actual prompt text (e.g. "You are a helpful assistant...")
    created_at = Column(DateTime, default=datetime.utcnow)