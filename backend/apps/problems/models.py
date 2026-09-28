from django.db import models

class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField()
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES, db_index=True)
    topics = models.JSONField(default=list)
    patterns = models.JSONField(default=list)
    constraints = models.JSONField(default=list)
    examples = models.JSONField(default=list)
    starter_code = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.title} ({self.difficulty})"

class TestCase(models.Model):
    __test__ = False # Prevent Pytest from trying to collect model as a test suite

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='test_cases',
        db_index=True
    )
    input_data = models.TextField(help_text="Inputs formatted as Python statements or JSON strings")
    expected_output = models.TextField()
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"TestCase {self.id} for {self.problem.slug} (Public: {self.is_public})"
