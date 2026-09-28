from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.schemas.problem import ProblemListItem

class ProgressAttemptRequest(BaseModel):
    status: str # SOLVED, ATTEMPTED, UNSOLVED
    time_spent: Optional[int] = 0
    code: Optional[str] = None

class UserProblemProgressResponse(BaseModel):
    id: int
    user_id: int
    problem_id: int
    status: str
    attempts: int
    solved_at: Optional[datetime] = None
    time_spent: int
    hints_used: int
    hint_level: int

    model_config = ConfigDict(from_attributes=True)

class TopicProgressItem(BaseModel):
    topic: str
    solved: int
    total: int
    percentage: float

class DashboardStatsResponse(BaseModel):
    total_problems: int
    solved_count: int
    attempted_count: int
    current_streak: int
    topic_progress: List[TopicProgressItem]
    recent_problems: List[ProblemListItem]
    recommended_problem: Optional[ProblemListItem] = None
