from django.db import models
from django.conf import settings
from apps.problems.models import Problem

class UserProblemProgress(models.Model):
    STATUS_CHOICES = [
        ('UNSOLVED', 'Unsolved'),
        ('ATTEMPTED', 'Attempted'),
        ('SOLVED', 'Solved'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='progress_entries',
        db_index=True
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='progress_entries',
        db_index=True
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='UNSOLVED')
    attempts = models.IntegerField(default=0)
    solved_at = models.DateTimeField(null=True, blank=True)
    time_spent = models.IntegerField(default=0) # in seconds

    # Prepared for future AI coaching phases
    hints_used = models.IntegerField(default=0)
    hint_level = models.IntegerField(default=0)
    challenge_score = models.FloatField(null=True, blank=True)
    interview_score = models.FloatField(null=True, blank=True)
    submission_history = models.JSONField(default=list)

    class Meta:
        unique_together = ('user', 'problem')
        ordering = ['-id']

    def __str__(self):
        return f"{self.user.email} - {self.problem.slug} ({self.status})"
