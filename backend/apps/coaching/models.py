from django.db import models
from django.conf import settings
from apps.problems.models import Problem
from apps.submissions.models import Submission

class CoachingSession(models.Model):
    LEARNING_STAGES = [
        ('UNDERSTANDING_PROBLEM', 'Understanding Problem'),
        ('APPROACH_DISCOVERY', 'Approach Discovery'),
        ('GUIDED_IMPLEMENTATION', 'Guided Implementation'),
        ('DEBUGGING', 'Debugging'),
        ('CORRECTNESS_VERIFICATION', 'Correctness Verification'),
        ('COMPLEXITY_ANALYSIS', 'Complexity Analysis'),
        ('OPTIMIZATION_DISCOVERY', 'Optimization Discovery'),
        ('OPTIMIZED_IMPLEMENTATION', 'Optimized Implementation'),
        ('APPROACH_COMPARISON', 'Approach Comparison'),
        ('COMPLETED', 'Completed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coaching_sessions',
        db_index=True
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='coaching_sessions',
        db_index=True
    )
    stage = models.CharField(
        max_length=50,
        choices=LEARNING_STAGES,
        default='APPROACH_DISCOVERY',
        db_index=True
    )
    current_approach = models.JSONField(
        default=dict,
        blank=True,
        help_text="Current approach details: name, type, is_valid, is_optimal, complexity, description"
    )
    explored_approaches = models.JSONField(
        default=list,
        blank=True,
        help_text="List of previously or currently explored approaches with status and complexity"
    )
    solution_status = models.CharField(
        max_length=50,
        default='IN_PROGRESS',
        db_index=True
    )
    complexity_state = models.JSONField(
        default=dict,
        blank=True,
        help_text="Time and space complexity discussion and validated values"
    )
    hints_provided = models.JSONField(
        default=list,
        blank=True,
        help_text="List of previous clues/hints given to avoid repetition"
    )
    misconceptions = models.JSONField(
        default=list,
        blank=True,
        help_text="Misconceptions identified during session"
    )
    last_student_code = models.TextField(blank=True, default='')
    last_execution_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'problem')
        ordering = ['-updated_at']

    def __str__(self):
        return f"CoachingSession for {self.user.email} on {self.problem.slug} ({self.stage})"


class CoachingInteraction(models.Model):
    INTERACTION_TYPES = [
        ('chat', 'Conversational Chat'),
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
    coaching_session = models.ForeignKey(
        CoachingSession,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='interactions'
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

