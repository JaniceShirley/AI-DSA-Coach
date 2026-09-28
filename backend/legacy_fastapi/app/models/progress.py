from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.base import Base

class UserProblemProgress(Base):
    __tablename__ = "user_problem_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # UNSOLVED, ATTEMPTED, SOLVED
    status = Column(String(50), nullable=False, default="UNSOLVED")
    attempts = Column(Integer, nullable=False, default=0)
    solved_at = Column(DateTime(timezone=True), nullable=True)
    time_spent = Column(Integer, nullable=False, default=0) # in seconds

    # Fields prepared for future phases (hints, scoring, interview)
    hints_used = Column(Integer, nullable=False, default=0)
    hint_level = Column(Integer, nullable=False, default=0)
    challenge_score = Column(Float, nullable=True)
    interview_score = Column(Float, nullable=True)
    submission_history = Column(JSON, nullable=False, default=list)

    user = relationship("User", back_populates="progress_entries")
    problem = relationship("Problem", back_populates="progress_entries")

    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", name="uix_user_problem"),
    )
