from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.progress import DashboardStatsResponse, UserProblemProgressResponse, ProgressAttemptRequest
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/progress", tags=["User Progress"])

@router.get("", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aggregated dashboard metrics for the logged-in user."""
    return ProgressService.get_dashboard_stats(db=db, user_id=current_user.id)

@router.get("/{problem_id}", response_model=UserProblemProgressResponse)
def get_problem_progress(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user progress for a specific problem."""
    return ProgressService.get_user_progress_for_problem(
        db=db, user_id=current_user.id, problem_id=problem_id
    )

@router.post("/{problem_id}/attempt", response_model=UserProblemProgressResponse)
def record_problem_attempt(
    problem_id: int,
    attempt_in: ProgressAttemptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a submission attempt or solution for a problem."""
    return ProgressService.record_attempt(
        db=db,
        user_id=current_user.id,
        problem_id=problem_id,
        status=attempt_in.status,
        time_spent=attempt_in.time_spent or 0,
        code=attempt_in.code
    )
