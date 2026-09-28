from django.db import models
from django.conf import settings
from apps.problems.models import Problem

class Submission(models.Model):
    STATUS_CHOICES = [
        ('ACCEPTED', 'Accepted'),
        ('WRONG_ANSWER', 'Wrong Answer'),
        ('RUNTIME_ERROR', 'Runtime Error'),
        ('SYNTAX_ERROR', 'Syntax Error'),
        ('TIME_LIMIT_EXCEEDED', 'Time Limit Exceeded'),
        ('INTERNAL_ERROR', 'Internal Error'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions',
        db_index=True
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='submissions',
        db_index=True
    )
    code = models.TextField()
    language = models.CharField(max_length=50, default='python')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, db_index=True)
    runtime = models.FloatField(default=0.0, help_text="Runtime in milliseconds")
    memory = models.FloatField(default=0.0, help_text="Memory usage in MB")
    error_message = models.TextField(null=True, blank=True)
    test_cases_passed = models.IntegerField(default=0)
    total_test_cases = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Submission #{self.id} by {self.user.email} for {self.problem.slug} ({self.status})"
