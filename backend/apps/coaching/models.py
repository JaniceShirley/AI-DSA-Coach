from django.db import models
from django.conf import settings
from apps.problems.models import Problem
from apps.submissions.models import Submission

class CoachingInteraction(models.Model):
    INTERACTION_TYPES = [
        ('hint', 'Hint'),
        ('challenge', 'Challenge'),
        ('alternative', 'Alternative Approach'),
        ('feedback', 'AI Feedback'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coaching_interactions',
        db_index=True
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='coaching_interactions',
        db_index=True
    )
    session_id = models.CharField(max_length=100, db_index=True)
    student_code = models.TextField(blank=True, default='')
    hint_level = models.IntegerField(null=True, blank=True)
    user_question = models.TextField(null=True, blank=True)
    ai_response = models.TextField()
    submission = models.ForeignKey(
        Submission,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='coaching_interactions'
    )
    interaction_type = models.CharField(
        max_length=50,
        choices=INTERACTION_TYPES,
        default='hint',
        db_index=True
    )
    evaluation_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Evaluation metadata (relevance, correctness, hint_specificity, solution_leakage, helpfulness)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"CoachingInteraction #{self.id} ({self.interaction_type}) for {self.user.email} on {self.problem.slug}"
