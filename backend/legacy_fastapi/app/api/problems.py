from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.deps import get_current_user_optional
from app.models.user import User
from app.schemas.problem import ProblemResponse, ProblemListItem
from app.services.problem_service import ProblemService

router = APIRouter(prefix="/problems", tags=["Problems"])

@router.get("", response_model=List[ProblemListItem])
def list_problems(
    search: Optional[str] = Query(None, description="Search term for title or description"),
    difficulty: Optional[str] = Query(None, description="Filter by Easy, Medium, Hard"),
    topic: Optional[str] = Query(None, description="Filter by Topic name"),
    status_filter: Optional[str] = Query(None, description="Filter by status: UNSOLVED, ATTEMPTED, SOLVED"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Retrieve list of curated DSA problems with filters."""
    user_id = current_user.id if current_user else None
    return ProblemService.get_problems(
        db=db,
        user_id=user_id,
        search=search,
        difficulty=difficulty,
        topic=topic,
        status_filter=status_filter
    )

@router.get("/{slug}", response_model=ProblemResponse)
def get_problem(slug: str, db: Session = Depends(get_db)):
    """Get problem details by unique slug."""
    problem = ProblemService.get_problem_by_slug(db=db, slug=slug)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem with slug '{slug}' not found"
        )
    return problem
