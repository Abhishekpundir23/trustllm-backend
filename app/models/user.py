from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # 👇 NEW: Store API Keys
    openai_key = Column(String, nullable=True)
    anthropic_key = Column(String, nullable=True)
    gemini_key = Column(String, nullable=True)

    projects = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan"
    )