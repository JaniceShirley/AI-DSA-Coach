from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.problem import Problem
from app.models.progress import UserProblemProgress
from app.schemas.problem import ProblemListItem, ProblemResponse

class ProblemService:
    @staticmethod
    def get_problems(
        db: Session,
        user_id: Optional[int] = None,
        search: Optional[str] = None,
        difficulty: Optional[str] = None,
        topic: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[ProblemListItem]:
        query = db.query(Problem)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Problem.title.ilike(search_pattern),
                    Problem.description.ilike(search_pattern)
                )
            )

        if difficulty and difficulty != "All":
            query = query.filter(Problem.difficulty.ilike(difficulty))

        problems = query.order_by(Problem.id.asc()).all()

        # Load user progress mapping if user is logged in
        progress_map = {}
        if user_id:
            progress_entries = db.query(UserProblemProgress).filter(
                UserProblemProgress.user_id == user_id
            ).all()
            progress_map = {p.problem_id: p.status for p in progress_entries}

        result = []
        for problem in problems:
            # Topic filtering post-query if JSON field or search
            if topic and topic != "All":
                if topic not in (problem.topics or []):
                    continue

            user_status = progress_map.get(problem.id, "UNSOLVED")

            if status_filter and status_filter != "All":
                if status_filter.upper() != user_status:
                    continue

            result.append(ProblemListItem(
                id=problem.id,
                title=problem.title,
                slug=problem.slug,
                difficulty=problem.difficulty,
                topics=problem.topics or [],
                patterns=problem.patterns or [],
                user_status=user_status
            ))

        return result

    @staticmethod
    def get_problem_by_slug(db: Session, slug: str) -> Optional[Problem]:
        return db.query(Problem).filter(Problem.slug == slug).first()

    @staticmethod
    def get_problem_by_id(db: Session, problem_id: int) -> Optional[Problem]:
        return db.query(Problem).filter(Problem.id == problem_id).first()
