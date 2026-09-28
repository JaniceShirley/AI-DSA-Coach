import pytest
from django.core.management import call_command
from apps.problems.models import Problem

@pytest.mark.django_db
class TestSeedingCommand:
    def test_seed_problems_does_not_create_duplicates(self):
        # Run seeding first time
        call_command('seed_problems')
        initial_count = Problem.objects.count()
        assert initial_count == 30

        # Run seeding second time
        call_command('seed_problems')
        second_count = Problem.objects.count()
        assert second_count == 30
