import re
import logging
from typing import Dict, Any, List, Optional
from django.conf import settings
from apps.problems.models import Problem
from apps.submissions.models import Submission
from apps.progress.models import UserProblemProgress
from apps.coaching.models import CoachingInteraction
from apps.coaching.providers import get_ai_provider

logger = logging.getLogger(__name__)

class AICoachService:
    """
    Dedicated service for AI coaching logic.
    Decoupled from Django views and model providers.
    """

    def __init__(self):
        self.provider = get_ai_provider()

    def _get_session_id(self, user_id: int, problem_id: int) -> str:
        return f"session_{user_id}_{problem_id}"

    def _sanitize_response(self, text: str) -> str:
        """
        Solution Leakage Prevention:
        Sanitize response if model accidentally outputs complete runnable function implementations.
        """
        if not text:
            return "AI Coach is analyzing your approach..."

        # Pattern to detect complete code blocks containing full solution implementations
        code_block_pattern = r'```(?:python|py)?\s*(def\s+\w+\s*\(.*?\):[\s\S]*?)```'
        matches = re.findall(code_block_pattern, text)
        for match in matches:
            # If code block is long (> 8 lines or contains complete solution structure), replace it
            lines = match.strip().split('\n')
            if len(lines) > 8 or ('return' in match and len(lines) > 5):
                replacement = (
                    "```python\n"
                    "# [Full solution code withheld by AI Coach to encourage independent problem solving]\n"
                    "# Think about how to structure these steps into your own code!\n"
                    "```"
                )
                text = text.replace(f"```{lines[0]}", replacement)

        return text

    def _get_latest_submission(self, user, problem, submission_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        sub = None
        if submission_id:
            sub = Submission.objects.filter(id=submission_id, user=user, problem=problem).first()
        if not sub:
            sub = Submission.objects.filter(user=user, problem=problem).first()

        if sub:
            return {
                "id": sub.id,
                "status": sub.status,
                "runtime": sub.runtime,
                "memory": sub.memory,
                "test_cases_passed": sub.test_cases_passed,
                "total_test_cases": sub.total_test_cases,
                "error_message": sub.error_message,
            }
        return None

    def _get_previous_hints(self, user, problem) -> List[str]:
        interactions = CoachingInteraction.objects.filter(
            user=user,
            problem=problem,
            interaction_type='hint'
        ).order_by('-created_at')[:5]
        return [item.ai_response for item in reversed(list(interactions))]

    def generate_hint(
        self,
        user,
        problem: Problem,
        student_code: str,
        submission_id: Optional[int] = None,
        requested_level: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate progressive hint (Levels 1-4) based on student code and attempt history."""
        session_id = self._get_session_id(user.id, problem.id)
        progress, _ = UserProblemProgress.objects.get_or_create(user=user, problem=problem)

        # Progression logic:
        if requested_level is not None:
            current_level = min(max(requested_level, 1), 4)
        else:
            if progress.hint_level == 0:
                current_level = 1
            elif progress.hint_level < 4:
                current_level = progress.hint_level + 1
            else:
                current_level = 4

        progress.hint_level = current_level
        progress.hints_used = (progress.hints_used or 0) + 1
        progress.save(update_fields=['hint_level', 'hints_used'])

        latest_sub = self._get_latest_submission(user, problem, submission_id)
        prev_hints = self._get_previous_hints(user, problem)

        context = {
            "problem": {
                "id": problem.id,
                "title": problem.title,
                "description": problem.description,
                "difficulty": problem.difficulty,
                "topics": problem.topics,
                "patterns": problem.patterns,
                "constraints": problem.constraints,
                "examples": problem.examples,
            },
            "student_code": student_code,
            "language": "python",
            "latest_submission": latest_sub,
            "previous_attempts": progress.attempts,
            "previous_hints": prev_hints,
            "hint_level": current_level,
            "user_progress": {
                "status": progress.status,
                "attempts": progress.attempts,
                "hints_used": progress.hints_used,
            }
        }

        try:
            raw_response = self.provider.generate_hint(context)
            ai_response = self._sanitize_response(raw_response)
        except Exception as e:
            logger.error(f"AI Coach hint generation error for user {user.id}: {e}")
            ai_response = "AI Coach is temporarily unavailable. You can continue solving and submit your code normally."

        submission_obj = Submission.objects.filter(id=submission_id).first() if submission_id else None

        interaction = CoachingInteraction.objects.create(
            user=user,
            problem=problem,
            session_id=session_id,
            student_code=student_code,
            hint_level=current_level,
            ai_response=ai_response,
            submission=submission_obj,
            interaction_type='hint',
            evaluation_metadata={
                "relevance": None,
                "correctness": None,
                "hint_specificity": current_level,
                "solution_leakage": False,
                "helpfulness": None
            }
        )

        return {
            "status": "success",
            "interaction_id": interaction.id,
            "session_id": session_id,
            "hint": ai_response,
            "hint_level": current_level,
            "hints_used": progress.hints_used,
        }

    def challenge_understanding(
        self,
        user,
        problem: Problem,
        student_code: str,
        user_answer: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate conceptual edge-case challenge questions or evaluate student answers."""
        session_id = self._get_session_id(user.id, problem.id)
        latest_sub = self._get_latest_submission(user, problem)

        context = {
            "problem": {
                "id": problem.id,
                "title": problem.title,
                "description": problem.description,
            },
            "student_code": student_code,
            "user_question": user_answer or "",
            "latest_submission": latest_sub,
        }

        try:
            raw_response = self.provider.challenge_understanding(context)
            ai_response = self._sanitize_response(raw_response)
        except Exception as e:
            logger.error(f"AI Coach challenge error for user {user.id}: {e}")
            ai_response = "AI Coach is temporarily unavailable. You can continue solving and submit your code normally."

        interaction = CoachingInteraction.objects.create(
            user=user,
            problem=problem,
            session_id=session_id,
            student_code=student_code,
            user_question=user_answer,
            ai_response=ai_response,
            interaction_type='challenge',
            evaluation_metadata={"relevance": None, "correctness": None, "solution_leakage": False}
        )

        return {
            "status": "success",
            "interaction_id": interaction.id,
            "session_id": session_id,
            "challenge": ai_response,
        }

    def generate_alternative_approach(
        self,
        user,
        problem: Problem,
        student_code: str
    ) -> Dict[str, Any]:
        """Explain alternative valid algorithmic strategies and trade-offs."""
        session_id = self._get_session_id(user.id, problem.id)

        context = {
            "problem": {
                "id": problem.id,
                "title": problem.title,
                "description": problem.description,
            },
            "student_code": student_code,
        }

        try:
            raw_response = self.provider.generate_alternative_approach(context)
            ai_response = self._sanitize_response(raw_response)
        except Exception as e:
            logger.error(f"AI Coach alternative approach error for user {user.id}: {e}")
            ai_response = "AI Coach is temporarily unavailable. You can continue solving and submit your code normally."

        interaction = CoachingInteraction.objects.create(
            user=user,
            problem=problem,
            session_id=session_id,
            student_code=student_code,
            ai_response=ai_response,
            interaction_type='alternative',
            evaluation_metadata={"relevance": None, "solution_leakage": False}
        )

        return {
            "status": "success",
            "interaction_id": interaction.id,
            "session_id": session_id,
            "alternative_approach": ai_response,
        }

    def generate_feedback(
        self,
        user,
        problem: Problem,
        student_code: str,
        submission_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Evaluate accuracy, complexity, edge cases, and code quality after submission."""
        session_id = self._get_session_id(user.id, problem.id)
        latest_sub = self._get_latest_submission(user, problem, submission_id)

        context = {
            "problem": {
                "id": problem.id,
                "title": problem.title,
                "description": problem.description,
            },
            "student_code": student_code,
            "latest_submission": latest_sub,
        }

        try:
            feedback_data = self.provider.generate_feedback(context)
        except Exception as e:
            logger.error(f"AI Coach feedback error for user {user.id}: {e}")
            feedback_data = {
                "approach": "AI Coach is temporarily unavailable.",
                "correctness": "You can continue solving and submit your code normally.",
                "time_complexity": "N/A",
                "space_complexity": "N/A",
                "edge_cases": "N/A",
                "optimization": "N/A"
            }

        submission_obj = Submission.objects.filter(id=submission_id).first() if submission_id else None

        interaction = CoachingInteraction.objects.create(
            user=user,
            problem=problem,
            session_id=session_id,
            student_code=student_code,
            ai_response=str(feedback_data),
            submission=submission_obj,
            interaction_type='feedback',
            evaluation_metadata={"relevance": None, "solution_leakage": False}
        )

        return {
            "status": "success",
            "interaction_id": interaction.id,
            "session_id": session_id,
            "feedback": feedback_data,
        }

ai_coach_service = AICoachService()
