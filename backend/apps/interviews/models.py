from django.db import models
from django.conf import settings
from apps.problems.models import Problem
from apps.submissions.models import Submission

class InterviewSession(models.Model):
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ABANDONED', 'Abandoned'),
    ]

    STAGE_CHOICES = [
        ('PROBLEM_INTRO', 'Problem Introduction'),
        ('APPROACH', 'Approach & Data Structures'),
        ('COMPLEXITY', 'Complexity Analysis'),
        ('EDGE_CASES', 'Edge Cases'),
        ('OPTIMIZATION', 'Optimization & Trade-offs'),
        ('CODING', 'Coding Implementation'),
        ('FINAL_EVALUATION', 'Final Evaluation'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interview_sessions',
        db_index=True
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='interview_sessions',
        db_index=True
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='IN_PROGRESS',
        db_index=True
    )
    difficulty = models.CharField(max_length=20, default='Easy')
    current_stage = models.CharField(
        max_length=50,
        choices=STAGE_CHOICES,
        default='PROBLEM_INTRO',
        db_index=True
    )
    submission = models.ForeignKey(
        Submission,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='interview_sessions'
    )
    final_feedback = models.TextField(blank=True, default='')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"InterviewSession #{self.id} for {self.user.email} on {self.problem.title} ({self.status})"

class InterviewMessage(models.Model):
    ROLE_CHOICES = [
        ('AI_INTERVIEWER', 'AI Interviewer'),
        ('STUDENT', 'Student'),
    ]

    interview_session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='messages',
        db_index=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, db_index=True)
    message = models.TextField()
    stage = models.CharField(max_length=50, default='PROBLEM_INTRO')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message #{self.id} [{self.role}] ({self.stage})"

class InterviewEvaluation(models.Model):
    interview_session = models.OneToOneField(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='evaluation',
        db_index=True
    )
    problem_understanding = models.JSONField(default=dict)
    approach_quality = models.JSONField(default=dict)
    technical_reasoning = models.JSONField(default=dict)
    complexity_analysis = models.JSONField(default=dict)
    edge_case_awareness = models.JSONField(default=dict)
    optimization = models.JSONField(default=dict)
    communication = models.JSONField(default=dict)
    coding_correctness = models.JSONField(default=dict)
    overall_score = models.IntegerField(default=85, help_text="Rubric score out of 100")
    strengths = models.JSONField(default=list)
    areas_for_improvement = models.JSONField(default=list)
    final_feedback = models.TextField(blank=True, default='')
    recommended_topics = models.JSONField(default=list)
    recommended_problems = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluation for Session #{self.interview_session_id} (Score: {self.overall_score})"
