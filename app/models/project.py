from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    domain = Column(String, default="general")

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="projects")
    
    tests = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")
    
    # NEW: Relationship to prompts
    prompts = relationship("PromptVersion", backref="project", cascade="all, delete-orphan")