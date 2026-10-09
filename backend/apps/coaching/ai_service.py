import re
import logging
from typing import Dict, Any, List, Optional
from django.conf import settings
from apps.problems.models import Problem
from apps.submissions.models import Submission
from apps.progress.models import UserProblemProgress
from apps.coaching.models import CoachingInteraction, CoachingSession
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

    def get_or_create_session(self, user, problem: Problem) -> CoachingSession:
        session, _ = CoachingSession.objects.get_or_create(
            user=user,
            problem=problem,
            defaults={
                'stage': 'APPROACH_DISCOVERY',
                'current_approach': {},
                'explored_approaches': [],
                'solution_status': 'IN_PROGRESS',
                'complexity_state': {},
                'hints_provided': [],
                'misconceptions': [],
            }
        )
        return session

    def get_session_state(self, user, problem: Problem) -> Dict[str, Any]:
        session = self.get_or_create_session(user, problem)
        interactions = CoachingInteraction.objects.filter(
            user=user,
            problem=problem,
            interaction_type='chat'
        ).order_by('created_at')

        messages = []
        for inter in interactions:
            if inter.user_question:
                messages.append({
                    "id": f"{inter.id}-user",
                    "role": "user",
                    "content": inter.user_question,
                    "created_at": inter.created_at.isoformat()
                })
            messages.append({
                "id": f"{inter.id}-ai",
                "role": "assistant",
                "content": inter.ai_response,
                "created_at": inter.created_at.isoformat()
            })

        return {
            "session_id": session.id,
            "problem_id": problem.id,
            "stage": session.stage,
            "current_approach": session.current_approach,
            "explored_approaches": session.explored_approaches,
            "solution_status": session.solution_status,
            "complexity_state": session.complexity_state,
            "hints_provided": session.hints_provided,
            "misconceptions": session.misconceptions,
            "last_student_code": session.last_student_code,
            "last_execution_result": session.last_execution_result,
            "messages": messages,
            "updated_at": session.updated_at.isoformat()
        }

    def reset_session(self, user, problem: Problem) -> Dict[str, Any]:
        session = self.get_or_create_session(user, problem)
        session.stage = 'APPROACH_DISCOVERY'
        session.current_approach = {}
        session.explored_approaches = []
        session.solution_status = 'IN_PROGRESS'
        session.complexity_state = {}
        session.hints_provided = []
        session.misconceptions = []
        session.last_student_code = ''
        session.last_execution_result = {}
        session.save()

        # Archive or clear prior chat interactions for fresh start
        CoachingInteraction.objects.filter(user=user, problem=problem, interaction_type='chat').delete()

        return self.get_session_state(user, problem)

    def chat(
        self,
        user,
        problem: Problem,
        message: str,
        student_code: str = "",
        run_code: bool = False
    ) -> Dict[str, Any]:
        session = self.get_or_create_session(user, problem)
        session_id_str = self._get_session_id(user.id, problem.id)

        # Retrieve bounded dialogue history (last 8 chat turns)
        recent_interactions = CoachingInteraction.objects.filter(
            user=user,
            problem=problem,
            interaction_type='chat'
        ).order_by('-created_at')[:8]

        dialogue_history = []
        for item in reversed(list(recent_interactions)):
            dialogue_history.append({
                "user": item.user_question or "",
                "assistant": item.ai_response or ""
            })

        session_data = {
            "stage": session.stage,
            "current_approach": session.current_approach,
            "explored_approaches": session.explored_approaches,
            "solution_status": session.solution_status,
            "complexity_state": session.complexity_state,
            "hints_provided": session.hints_provided,
            "misconceptions": session.misconceptions,
            "dialogue_history": dialogue_history,
        }

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
            "problem_obj": problem,
            "session_data": session_data,
            "student_message": message,
            "student_code": student_code,
            "run_code": run_code,
        }

        try:
            turn_result = self.provider.conduct_chat_turn(context)
            raw_ai_message = turn_result.get("message", "")
            ai_message = self._sanitize_response(raw_ai_message)
        except Exception as e:
            logger.error(f"Error conducting chat turn for user {user.id} on problem {problem.id}: {e}")
            ai_message = "I encountered an issue processing your response. Let's continue—what step would you like to explore next?"
            turn_result = {
                "stage": session.stage,
                "current_approach": session.current_approach,
                "explored_approaches": session.explored_approaches,
                "solution_status": session.solution_status,
                "complexity_state": session.complexity_state,
                "hints_provided": session.hints_provided,
                "misconceptions": session.misconceptions,
                "execution_result": None
            }

        # Update and save session state
        session.stage = turn_result.get("stage", session.stage)
        session.current_approach = turn_result.get("current_approach", session.current_approach)
        session.explored_approaches = turn_result.get("explored_approaches", session.explored_approaches)
        session.solution_status = turn_result.get("solution_status", session.solution_status)
        session.complexity_state = turn_result.get("complexity_state", session.complexity_state)
        session.hints_provided = turn_result.get("hints_provided", session.hints_provided)
        session.misconceptions = turn_result.get("misconceptions", session.misconceptions)
        if student_code:
            session.last_student_code = student_code
        if turn_result.get("execution_result"):
            session.last_execution_result = turn_result.get("execution_result")
        session.save()

        # Record interaction
        interaction = CoachingInteraction.objects.create(
            user=user,
            problem=problem,
            coaching_session=session,
            session_id=session_id_str,
            student_code=student_code,
            user_question=message,
            ai_response=ai_message,
            interaction_type='chat',
            evaluation_metadata={
                "stage": session.stage,
                "approach": session.current_approach.get("name") if session.current_approach else None
            }
        )

        return {
            "status": "success",
            "message": ai_message,
            "stage": session.stage,
            "current_approach": session.current_approach,
            "explored_approaches": session.explored_approaches,
            "solution_status": session.solution_status,
            "complexity_state": session.complexity_state,
            "execution_result": turn_result.get("execution_result"),
            "interaction_id": interaction.id,
            "session_id": session.id
        }

ai_coach_service = AICoachService()

