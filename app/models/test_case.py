from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class TestCase(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    
    # Replaced 'name' with the actual fields used in your API and Schema
    prompt = Column(Text, nullable=False)
    task_type = Column(String, nullable=False)
    rules = Column(JSON, nullable=True)
    expected = Column(Text, nullable=True)

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    project = relationship("Project", back_populates="tests")