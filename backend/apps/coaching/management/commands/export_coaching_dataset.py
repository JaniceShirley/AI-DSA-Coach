import os
import json
from django.core.management.base import BaseCommand
from apps.coaching.models import CoachingInteraction

class Command(BaseCommand):
    help = 'Exports coaching interactions into a structured JSONL dataset for future QLoRA/LLM fine-tuning foundation.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='coaching_dataset.jsonl',
            help='Output file path for the exported JSONL dataset.'
        )
        parser.add_argument(
            '--type',
            type=str,
            default=None,
            help='Filter by interaction type (hint, challenge, alternative, feedback).'
        )

    def handle(self, *args, **options):
        output_path = options['output']
        interaction_type = options['type']

        queryset = CoachingInteraction.objects.select_related('user', 'problem').all()
        if interaction_type:
            queryset = queryset.filter(interaction_type=interaction_type)

        count = queryset.count()
        self.stdout.write(f"Exporting {count} coaching interactions to {output_path}...")

        exported_rows = 0
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in queryset:
                record = {
                    "interaction_id": item.id,
                    "user_id": item.user.id,
                    "problem": {
                        "id": item.problem.id,
                        "title": item.problem.title,
                        "slug": item.problem.slug,
                        "difficulty": item.problem.difficulty,
                    },
                    "student_code": item.student_code,
                    "hint_level": item.hint_level,
                    "student_question": item.user_question,
                    "coach_response": item.ai_response,
                    "interaction_type": item.interaction_type,
                    "submission_id": item.submission.id if item.submission else None,
                    "evaluation_metadata": item.evaluation_metadata or {
                        "relevance": None,
                        "correctness": None,
                        "hint_specificity": item.hint_level,
                        "solution_leakage": False,
                        "helpfulness": None,
                    },
                    "created_at": item.created_at.isoformat(),
                }
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
                exported_rows += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully exported {exported_rows} records to {output_path}."))
