import os
import json
import re
from pathlib import Path
from django.core.management.base import BaseCommand
from apps.coaching.models import CoachingInteraction
from apps.interviews.models import InterviewSession, InterviewMessage, InterviewEvaluation

class Command(BaseCommand):
    help = 'Exports coaching and mock interview AI interactions into structured JSONL for ML fine-tuning & evaluation.'

    def add_arguments(self, parser):
        # Project root is parent of backend (6 levels up from this file)
        project_root = Path(__file__).resolve().parents[5]
        default_output = os.path.join(
            project_root,
            'ml', 'data', 'raw', 'raw_interactions.jsonl'
        )
        parser.add_argument(
            '--output',
            type=str,
            default=default_output,
            help=f'Output file path for the exported JSONL dataset (default: {default_output})'
        )
        parser.add_argument(
            '--validate',
            action='store_true',
            default=True,
            help='Run initial automated quality validation rules during export (default: True)'
        )
        parser.add_argument(
            '--no-validate',
            dest='validate',
            action='store_false',
            help='Do not run automated validation; mark all records as UNREVIEWED'
        )

    def _detect_code_leakage(self, text: str, hint_level: int = None) -> bool:
        """
        Detects if a coaching hint reveals complete runnable implementations prematurely.
        """
        if not text:
            return False
        # Full function definition with return statement (supports return type hints -> ...)
        has_def = bool(re.search(r'def\s+\w+\s*\([^)]*\)\s*(?:->[^:]+)?\s*:', text))
        has_return = 'return ' in text
        # If early hint (level 1 or 2) contains a full function definition or return block
        if hint_level in (1, 2) and has_def and has_return:
            return True
        # Complete markdown code block with > 6 lines and return
        code_blocks = re.findall(r'```(?:python|py)?([\s\S]*?)```', text)
        for block in code_blocks:
            lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
            if len(lines) >= 6 and 'return ' in block and has_def:
                return True
        return False

    def handle(self, *args, **options):
        output_path = options['output']
        run_validation = options['validate']

        # Ensure destination directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        exported_records = []
        seen_hashes = set()

        # 1. Fetch Coaching Interactions
        coaching_qs = CoachingInteraction.objects.select_related('user', 'problem', 'submission').all().order_by('created_at')
        self.stdout.write(f"Reading {coaching_qs.count()} coaching interactions...")

        for item in coaching_qs:
            prob = item.problem
            coach_resp = (item.ai_response or "").strip()
            student_code = (item.student_code or "").strip()
            student_q = (item.user_question or "").strip()

            rejection_reasons = []
            if not coach_resp:
                rejection_reasons.append("EMPTY_RESPONSE")
            elif len(coach_resp) < 15:
                rejection_reasons.append("EXTREMELY_SHORT_RESPONSE")

            if not prob or not prob.id:
                rejection_reasons.append("MISSING_PROBLEM")
            if not student_code and not student_q:
                rejection_reasons.append("MISSING_STUDENT_CONTEXT")
            if item.interaction_type not in ('hint', 'challenge', 'alternative', 'feedback'):
                rejection_reasons.append("INVALID_INTERACTION_TYPE")

            # Check duplicate
            record_key = (prob.id if prob else None, item.interaction_type, item.hint_level, student_q, coach_resp)
            if record_key in seen_hashes:
                rejection_reasons.append("DUPLICATE_RECORD")
            else:
                seen_hashes.add(record_key)

            # Solution leakage
            if self._detect_code_leakage(coach_resp, item.hint_level):
                rejection_reasons.append("COMPLETE_CODE_LEAKAGE")

            if not run_validation:
                val_status = "UNREVIEWED"
                qual_status = "PENDING_VALIDATION"
            else:
                if rejection_reasons:
                    val_status = "REJECTED"
                    qual_status = f"FLAGGED_{rejection_reasons[0]}"
                else:
                    val_status = "APPROVED"
                    qual_status = "PASSED_INITIAL_CHECKS"

            record = {
                "id": f"coach_{item.id}",
                "source": "coaching_interaction",
                "session_id": item.session_id,
                "user_id": item.user_id,
                "problem_id": prob.id if prob else None,
                "problem_title": prob.title if prob else "",
                "problem_slug": prob.slug if prob else "",
                "problem_description": prob.description if prob else "",
                "topic": prob.topics if prob else [],
                "difficulty": prob.difficulty.lower() if prob else "unknown",
                "student_code": item.student_code,
                "student_question": item.user_question or "",
                "hint_level": item.hint_level,
                "coach_response": item.ai_response,
                "interaction_type": item.interaction_type,
                "submission_id": item.submission_id,
                "validation_status": val_status,
                "quality_status": qual_status,
                "rejection_reasons": rejection_reasons,
                "created_at": item.created_at.isoformat()
            }
            exported_records.append(record)

        # 2. Fetch Interview Interactions (pair student responses with interviewer responses)
        interview_sessions = InterviewSession.objects.select_related('problem', 'user').prefetch_related('messages').all()
        self.stdout.write(f"Reading {interview_sessions.count()} interview sessions...")

        for session in interview_sessions:
            prob = session.problem
            messages = list(session.messages.all().order_by('created_at'))
            
            # Iterate through dialogue and extract student_response -> interviewer_response pairs
            for idx, msg in enumerate(messages):
                if msg.role == 'AI_INTERVIEWER' and idx > 0 and messages[idx - 1].role == 'STUDENT':
                    student_msg = messages[idx - 1]
                    interviewer_resp = msg.message.strip()
                    student_resp = student_msg.message.strip()

                    rejection_reasons = []
                    if not interviewer_resp:
                        rejection_reasons.append("EMPTY_RESPONSE")
                    elif len(interviewer_resp) < 15:
                        rejection_reasons.append("EXTREMELY_SHORT_RESPONSE")
                    if not prob or not prob.id:
                        rejection_reasons.append("MISSING_PROBLEM")
                    if not student_resp:
                        rejection_reasons.append("MISSING_STUDENT_CONTEXT")

                    record_key = (prob.id if prob else None, 'interview', msg.stage, student_resp, interviewer_resp)
                    if record_key in seen_hashes:
                        rejection_reasons.append("DUPLICATE_RECORD")
                    else:
                        seen_hashes.add(record_key)

                    if not run_validation:
                        val_status = "UNREVIEWED"
                        qual_status = "PENDING_VALIDATION"
                    else:
                        if rejection_reasons:
                            val_status = "REJECTED"
                            qual_status = f"FLAGGED_{rejection_reasons[0]}"
                        else:
                            val_status = "APPROVED"
                            qual_status = "PASSED_INITIAL_CHECKS"

                    record = {
                        "id": f"interview_{msg.id}",
                        "source": "interview_message",
                        "session_id": f"interview_session_{session.id}",
                        "user_id": session.user_id,
                        "problem_id": prob.id if prob else None,
                        "problem_title": prob.title if prob else "",
                        "problem_slug": prob.slug if prob else "",
                        "problem_description": prob.description if prob else "",
                        "topic": prob.topics if prob else [],
                        "difficulty": (session.difficulty or prob.difficulty).lower() if prob else "unknown",
                        "stage": msg.stage,
                        "student_response": student_resp,
                        "interviewer_response": interviewer_resp,
                        "interaction_type": "interview",
                        "validation_status": val_status,
                        "quality_status": qual_status,
                        "rejection_reasons": rejection_reasons,
                        "created_at": msg.created_at.isoformat()
                    }
                    exported_records.append(record)

        # Write to JSONL
        with open(output_path, 'w', encoding='utf-8') as f:
            for rec in exported_records:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')

        approved = sum(1 for r in exported_records if r['validation_status'] == 'APPROVED')
        rejected = sum(1 for r in exported_records if r['validation_status'] == 'REJECTED')
        unreviewed = sum(1 for r in exported_records if r['validation_status'] == 'UNREVIEWED')

        self.stdout.write(self.style.SUCCESS(
            f"Successfully exported {len(exported_records)} records to {output_path}.\n"
            f"Validation Summary -> APPROVED: {approved}, REJECTED: {rejected}, UNREVIEWED: {unreviewed}"
        ))
