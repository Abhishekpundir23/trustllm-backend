from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # Fix 1: Add the missing 'domain' column
    domain = Column(String, default="general")

    # Fix 2: Rename 'owner_id' to 'user_id' to match app/api/projects.py usage
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="projects")
    
    # Ensure this relationship from the previous fix is still here
    tests = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")