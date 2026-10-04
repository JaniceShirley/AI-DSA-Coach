import random
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from apps.problems.models import Problem
from apps.submissions.models import Submission
from apps.progress.models import UserProblemProgress
from apps.coaching.providers import get_ai_provider
from .models import InterviewSession, InterviewMessage, InterviewEvaluation
from .speech_normalizer import normalize_dsa_transcript

logger = logging.getLogger(__name__)

class InterviewService:
    """
    Service managing AI Mock Technical Interview orchestration, stage progression,
    dialogue turns, code association, and comprehensive rubric evaluation.
    """

    def __init__(self):
        self.provider = get_ai_provider()

    def start_interview(
        self,
        user,
        difficulty: Optional[str] = None,
        topic: Optional[str] = None,
        problem_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Start a new mock interview session and generate the initial opening message."""
        if problem_id:
            problem = Problem.objects.filter(id=problem_id).first()
            if not problem:
                raise ValueError(f"Problem with ID {problem_id} not found.")
        else:
            qs = Problem.objects.all()
            if difficulty and difficulty.lower() != 'any':
                qs = qs.filter(difficulty__iexact=difficulty)
            if topic and topic.lower() != 'any':
                qs = qs.filter(topics__contains=[topic])

            problems = list(qs)
            if not problems:
                problems = list(Problem.objects.all())

            if not problems:
                raise ValueError("No problems available in database for mock interview.")

            problem = random.choice(problems)

        session = InterviewSession.objects.create(
            user=user,
            problem=problem,
            difficulty=problem.difficulty,
            current_stage='PROBLEM_INTRO',
            status='IN_PROGRESS'
        )

        context = {
            "problem": {
                "id": problem.id,
                "title": problem.title,
                "description": problem.description,
                "difficulty": problem.difficulty,
                "topics": problem.topics,
            },
            "stage": "PROBLEM_INTRO",
            "student_message": "",
            "dialogue_history": [],
        }

        try:
            ai_turn = self.provider.conduct_interview_turn(context)
        except Exception as e:
            logger.error(f"Error starting interview AI turn for user {user.id}: {e}")
            ai_turn = {
                "stage": "APPROACH",
                "message": (
                    f"Hello! Welcome to your technical interview on **{problem.title}**.\n\n"
                    f"{problem.description}\n\n"
                    f"How would you approach solving this problem?"
                ),
                "should_advance_stage": True,
                "should_end": False
            }

        opening_message = InterviewMessage.objects.create(
            interview_session=session,
            role='AI_INTERVIEWER',
            message=ai_turn['message'],
            stage='PROBLEM_INTRO'
        )

        if ai_turn.get('should_advance_stage'):
            session.current_stage = ai_turn.get('stage', 'APPROACH')
            session.save(update_fields=['current_stage'])

        return {
            "session_id": session.id,
            "problem": {
                "id": problem.id,
                "title": problem.title,
                "slug": problem.slug,
                "difficulty": problem.difficulty,
                "description": problem.description,
                "topics": problem.topics,
                "constraints": problem.constraints,
                "examples": problem.examples,
                "starter_code": problem.starter_code,
            },
            "stage": session.current_stage,
            "status": session.status,
            "message": opening_message.message,
            "created_at": session.created_at.isoformat(),
        }

    def respond(self, session: InterviewSession, student_message: str) -> Dict[str, Any]:
        """Record candidate message, generate AI interviewer follow-up, and update interview stage."""
        if session.status != 'IN_PROGRESS':
            return {
                "session_id": session.id,
                "stage": session.current_stage,
                "status": session.status,
                "message": "This interview session has concluded.",
                "should_end": True
            }

        # Clean & normalize speech-to-text transcript
        cleaned_message = normalize_dsa_transcript(student_message) or student_message.strip()

        # Store student message
        InterviewMessage.objects.create(
            interview_session=session,
            role='STUDENT',
            message=cleaned_message,
            stage=session.current_stage
        )

        recent_msgs = session.messages.order_by('-created_at')[:8]
        history = [
            {"role": m.role, "message": m.message, "stage": m.stage}
            for m in reversed(list(recent_msgs))
        ]

        latest_sub_dict = None
        if session.submission:
            latest_sub_dict = {
                "id": session.submission.id,
                "status": session.submission.status,
                "test_cases_passed": session.submission.test_cases_passed,
                "total_test_cases": session.submission.total_test_cases,
                "runtime": session.submission.runtime,
            }

        context = {
            "problem": {
                "id": session.problem.id,
                "title": session.problem.title,
                "description": session.problem.description,
                "topics": session.problem.topics,
            },
            "stage": session.current_stage,
            "student_message": cleaned_message,
            "dialogue_history": history,
            "latest_submission": latest_sub_dict,
        }

        try:
            ai_turn = self.provider.conduct_interview_turn(context)
        except Exception as e:
            logger.error(f"Error in interview response AI turn: {e}")
            ai_turn = {
                "stage": session.current_stage,
                "message": "Thank you for that explanation. Could you walk me through the worst-case time complexity of your approach?",
                "should_advance_stage": False,
                "should_end": False
            }

        if ai_turn.get('should_advance_stage') and ai_turn.get('stage'):
            session.current_stage = ai_turn['stage']
            session.save(update_fields=['current_stage'])

        ai_message = InterviewMessage.objects.create(
            interview_session=session,
            role='AI_INTERVIEWER',
            message=ai_turn['message'],
            stage=session.current_stage
        )

        should_end = ai_turn.get('should_end', False)
        if should_end or session.current_stage == 'FINAL_EVALUATION':
            self.end_interview(session)

        return {
            "session_id": session.id,
            "stage": session.current_stage,
            "status": session.status,
            "message": ai_message.message,
            "should_end": should_end,
        }

    def associate_code_submission(self, session: InterviewSession, submission_id: int) -> Dict[str, Any]:
        """Attach code submission to interview session and generate interviewer feedback on the code execution."""
        submission = Submission.objects.filter(id=submission_id, user=session.user).first()
        if not submission:
            raise ValueError(f"Submission #{submission_id} not found for user {session.user.id}")

        session.submission = submission
        session.current_stage = 'CODING'
        session.save(update_fields=['submission', 'current_stage'])

        status_text = "Passed all automated test cases!" if submission.status == 'ACCEPTED' else f"Result: {submission.status} ({submission.test_cases_passed}/{submission.total_test_cases} passed)."
        interviewer_msg = (
            f"I have reviewed your implementation.\n\n"
            f"**Execution Status:** {status_text}\n"
            f"**Runtime:** {submission.runtime} ms | **Memory:** {submission.memory} MB\n\n"
            f"Let's move on to the final evaluation when you are ready."
        )

        InterviewMessage.objects.create(
            interview_session=session,
            role='AI_INTERVIEWER',
            message=interviewer_msg,
            stage='CODING'
        )

        return {
            "session_id": session.id,
            "submission_id": submission.id,
            "submission_status": submission.status,
            "message": interviewer_msg,
            "stage": session.current_stage,
        }

    def end_interview(self, session: InterviewSession) -> InterviewEvaluation:
        """Conclude mock technical interview and generate comprehensive performance evaluation report."""
        if hasattr(session, 'evaluation'):
            return session.evaluation

        session.status = 'COMPLETED'
        session.completed_at = timezone.now()
        session.current_stage = 'FINAL_EVALUATION'
        session.save(update_fields=['status', 'completed_at', 'current_stage'])

        # Build complete transcript
        all_messages = session.messages.order_by('created_at')
        transcript = [
            {"role": m.role, "message": m.message, "stage": m.stage}
            for m in all_messages
        ]

        latest_sub_dict = None
        if session.submission:
            latest_sub_dict = {
                "id": session.submission.id,
                "status": session.submission.status,
                "test_cases_passed": session.submission.test_cases_passed,
                "total_test_cases": session.submission.total_test_cases,
                "runtime": session.submission.runtime,
            }

        context = {
            "problem": {
                "id": session.problem.id,
                "title": session.problem.title,
                "topics": session.problem.topics,
                "difficulty": session.problem.difficulty,
            },
            "full_transcript": transcript,
            "latest_submission": latest_sub_dict,
        }

        try:
            eval_data = self.provider.evaluate_interview(context)
        except Exception as e:
            logger.error(f"Error generating interview evaluation for session {session.id}: {e}")
            eval_data = {
                "overall_score": 80,
                "problem_understanding": {"rating": "Good", "notes": "Solid understanding of requirements."},
                "approach_quality": {"rating": "Good", "notes": "Selected valid algorithmic approach."},
                "technical_reasoning": {"rating": "Good", "notes": "Articulated problem-solving logic clearly."},
                "complexity_analysis": {"rating": "Good", "notes": "Reasoned about time/space complexity."},
                "edge_case_awareness": {"rating": "Good", "notes": "Addressed key edge cases."},
                "optimization": {"rating": "Good", "notes": "Discussed optimizations and trade-offs."},
                "communication": {"rating": "Strong", "notes": "Professional and structured communication."},
                "coding_correctness": {"rating": "Good", "notes": "Implemented working solution."},
                "strengths": ["Structured thinking", "Clear communication"],
                "areas_for_improvement": ["Deeper edge case analysis"],
                "final_feedback": "Great interview performance! Keep practicing algorithmic complexity reasoning.",
                "recommended_topics": session.problem.topics,
                "recommended_problems": [],
            }

        # Find recommended unsolved problems
        rec_topics = eval_data.get('recommended_topics', session.problem.topics)
        solved_ids = UserProblemProgress.objects.filter(
            user=session.user, status='SOLVED'
        ).values_list('problem_id', flat=True)

        rec_problems = []
        matching_unsolved = Problem.objects.exclude(id__in=solved_ids).exclude(id=session.problem.id)
        for p in matching_unsolved:
            if any(t in (p.topics or []) for t in rec_topics):
                rec_problems.append({
                    "id": p.id,
                    "title": p.title,
                    "slug": p.slug,
                    "difficulty": p.difficulty
                })
                if len(rec_problems) >= 3:
                    break

        evaluation = InterviewEvaluation.objects.create(
            interview_session=session,
            problem_understanding=eval_data.get('problem_understanding', {}),
            approach_quality=eval_data.get('approach_quality', {}),
            technical_reasoning=eval_data.get('technical_reasoning', {}),
            complexity_analysis=eval_data.get('complexity_analysis', {}),
            edge_case_awareness=eval_data.get('edge_case_awareness', {}),
            optimization=eval_data.get('optimization', {}),
            communication=eval_data.get('communication', {}),
            coding_correctness=eval_data.get('coding_correctness', {}),
            overall_score=eval_data.get('overall_score', 85),
            strengths=eval_data.get('strengths', []),
            areas_for_improvement=eval_data.get('areas_for_improvement', []),
            final_feedback=eval_data.get('final_feedback', ''),
            recommended_topics=rec_topics,
            recommended_problems=rec_problems,
        )

        session.final_feedback = evaluation.final_feedback
        session.save(update_fields=['final_feedback'])

        return evaluation

interview_service = InterviewService()
