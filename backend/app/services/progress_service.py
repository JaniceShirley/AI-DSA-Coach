from datetime import datetime, timezone
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.progress import UserProblemProgress
from app.models.problem import Problem
from app.schemas.progress import DashboardStatsResponse, TopicProgressItem, UserProblemProgressResponse
from app.schemas.problem import ProblemListItem

class ProgressService:
    @staticmethod
    def get_user_progress_for_problem(db: Session, user_id: int, problem_id: int) -> UserProblemProgress:
        progress = db.query(UserProblemProgress).filter(
            UserProblemProgress.user_id == user_id,
            UserProblemProgress.problem_id == problem_id
        ).first()
        if not progress:
            progress = UserProblemProgress(
                user_id=user_id,
                problem_id=problem_id,
                status="UNSOLVED",
                attempts=0,
                time_spent=0
            )
            db.add(progress)
            db.commit()
            db.refresh(progress)
        return progress

    @staticmethod
    def record_attempt(
        db: Session,
        user_id: int,
        problem_id: int,
        status: str,
        time_spent: int = 0,
        code: Optional[str] = None
    ) -> UserProblemProgress:
        progress = db.query(UserProblemProgress).filter(
            UserProblemProgress.user_id == user_id,
            UserProblemProgress.problem_id == problem_id
        ).first()

        now = datetime.now(timezone.utc)
        if not progress:
            progress = UserProblemProgress(
                user_id=user_id,
                problem_id=problem_id,
                status=status.upper(),
                attempts=1,
                time_spent=time_spent
            )
            if status.upper() == "SOLVED":
                progress.solved_at = now
            if code:
                progress.submission_history = [{"code": code, "status": status, "timestamp": now.isoformat()}]
            db.add(progress)
        else:
            progress.attempts += 1
            progress.time_spent += time_spent
            # Upgrade status from UNSOLVED to ATTEMPTED/SOLVED, or ATTEMPTED to SOLVED
            if status.upper() == "SOLVED":
                progress.status = "SOLVED"
                if not progress.solved_at:
                    progress.solved_at = now
            elif progress.status != "SOLVED" and status.upper() == "ATTEMPTED":
                progress.status = "ATTEMPTED"

            if code:
                history = list(progress.submission_history or [])
                history.append({"code": code, "status": status, "timestamp": now.isoformat()})
                progress.submission_history = history

        db.commit()
        db.refresh(progress)
        return progress

    @staticmethod
    def get_dashboard_stats(db: Session, user_id: int) -> DashboardStatsResponse:
        total_problems = db.query(Problem).count()
        progress_entries = db.query(UserProblemProgress).filter(
            UserProblemProgress.user_id == user_id
        ).all()

        progress_map = {p.problem_id: p for p in progress_entries}
        solved_count = sum(1 for p in progress_entries if p.status == "SOLVED")
        attempted_count = len(progress_entries)

        # Basic streak calculation (if solved at least one problem, mock streak or count consecutive days)
        current_streak = 1 if solved_count > 0 else 0

        # Topic Breakdown
        all_problems = db.query(Problem).all()
        topic_totals: Dict[str, int] = {}
        topic_solved: Dict[str, int] = {}

        for p in all_problems:
            p_status = progress_map.get(p.id).status if p.id in progress_map else "UNSOLVED"
            for t in (p.topics or []):
                topic_totals[t] = topic_totals.get(t, 0) + 1
                if p_status == "SOLVED":
                    topic_solved[t] = topic_solved.get(t, 0) + 1

        topic_progress_list = []
        for t, total in topic_totals.items():
            solved = topic_solved.get(t, 0)
            percentage = round((solved / total) * 100, 1) if total > 0 else 0.0
            topic_progress_list.append(TopicProgressItem(
                topic=t,
                solved=solved,
                total=total,
                percentage=percentage
            ))

        # Recent problems
        recent_entries = sorted(
            [p for p in progress_entries if p.status in ["SOLVED", "ATTEMPTED"]],
            key=lambda x: x.solved_at or datetime.min,
            reverse=True
        )[:5]

        recent_problems = []
        for entry in recent_entries:
            prob = db.query(Problem).filter(Problem.id == entry.problem_id).first()
            if prob:
                recent_problems.append(ProblemListItem(
                    id=prob.id,
                    title=prob.title,
                    slug=prob.slug,
                    difficulty=prob.difficulty,
                    topics=prob.topics or [],
                    patterns=prob.patterns or [],
                    user_status=entry.status
                ))

        # Recommendation logic: First Easy or Medium unsolved problem
        recommended_problem = None
        unsolved_problems = [p for p in all_problems if p.id not in progress_map or progress_map[p.id].status != "SOLVED"]
        if unsolved_problems:
            rec = next((p for p in unsolved_problems if p.difficulty == "Easy"), unsolved_problems[0])
            recommended_problem = ProblemListItem(
                id=rec.id,
                title=rec.title,
                slug=rec.slug,
                difficulty=rec.difficulty,
                topics=rec.topics or [],
                patterns=rec.patterns or [],
                user_status=progress_map[rec.id].status if rec.id in progress_map else "UNSOLVED"
            )

        return DashboardStatsResponse(
            total_problems=total_problems,
            solved_count=solved_count,
            attempted_count=attempted_count,
            current_streak=current_streak,
            topic_progress=topic_progress_list,
            recent_problems=recent_problems,
            recommended_problem=recommended_problem
        )
