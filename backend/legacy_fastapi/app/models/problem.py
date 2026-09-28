from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, func
from sqlalchemy.orm import relationship
from app.database.base import Base

class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(50), index=True, nullable=False) # Easy, Medium, Hard
    topics = Column(JSON, nullable=False, default=list) # e.g. ["Array", "Hash Table"]
    patterns = Column(JSON, nullable=False, default=list) # e.g. ["Two Pointers"]
    constraints = Column(JSON, nullable=False, default=list) # List of constraints
    examples = Column(JSON, nullable=False, default=list) # List of example dicts
    starter_code = Column(JSON, nullable=False, default=dict) # {"python": "..."}
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    progress_entries = relationship("UserProblemProgress", back_populates="problem", cascade="all, delete-orphan")
