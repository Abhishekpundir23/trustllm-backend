from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class TestCase(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    
    prompt = Column(Text, nullable=False)
    
    # 👇 NEW: Context for RAG tests (The source text the AI should use)
    context = Column(Text, nullable=True) 
    
    task_type = Column(String, nullable=False)
    rules = Column(JSON, nullable=True)
    expected = Column(Text, nullable=True)

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    project = relationship("Project", back_populates="tests")