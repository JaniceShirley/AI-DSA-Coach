import os
import json
import pytest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient
from apps.problems.models import Problem
from apps.coaching.models import CoachingInteraction
from apps.progress.models import UserProblemProgress

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user():
    def _user(email="student@example.com", password="password123"):
        return User.objects.create_user(email=email, password=password)
    return _user

@pytest.fixture
def create_problem():
    def _problem(title="Two Sum", slug="two-sum"):
        return Problem.objects.create(
            title=title,
            slug=slug,
            description="Find two indices that sum up to target.",
            difficulty="Easy",
            topics=["Hash Table", "Array"],
            patterns=["Two Pointers"],
            starter_code={"python": "def twoSum(nums, target):\n    pass"}
        )
    return _problem

@pytest.mark.django_db
class TestCoachingAPI:

    def test_unauthenticated_user_cannot_access_coaching(self, api_client, create_problem):
        problem = create_problem()
        url = reverse('coaching-hint')
        response = api_client.post(url, {'problem_id': problem.id, 'student_code': 'def twoSum(): pass'})
        assert response.status_code == 401

    def test_authenticated_user_can_request_hint(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        url = reverse('coaching-hint')
        payload = {'problem_id': problem.id, 'student_code': 'def twoSum(nums, target): return []'}
        response = api_client.post(url, payload)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'hint' in data
        assert data['hint_level'] == 1
        assert data['hints_used'] == 1

    def test_hint_levels_progress_correctly(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)
        url = reverse('coaching-hint')

        payload = {'problem_id': problem.id, 'student_code': 'def twoSum(): pass'}

        res1 = api_client.post(url, payload).json()
        assert res1['hint_level'] == 1

        res2 = api_client.post(url, payload).json()
        assert res2['hint_level'] == 2

        res3 = api_client.post(url, payload).json()
        assert res3['hint_level'] == 3

        res4 = api_client.post(url, payload).json()
        assert res4['hint_level'] == 4

        # Max out at Level 4
        res5 = api_client.post(url, payload).json()
        assert res5['hint_level'] == 4
        assert res5['hints_used'] == 5

    def test_coaching_interaction_is_stored(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        url = reverse('coaching-hint')
        api_client.post(url, {'problem_id': problem.id, 'student_code': 'def twoSum(): pass'})

        interaction = CoachingInteraction.objects.filter(user=user, problem=problem).first()
        assert interaction is not None
        assert interaction.interaction_type == 'hint'
        assert interaction.hint_level == 1
        assert 'def twoSum(): pass' in interaction.student_code

    def test_user_cannot_access_another_user_coaching_history(self, api_client, create_user, create_problem):
        user1 = create_user(email="user1@example.com")
        user2 = create_user(email="user2@example.com")
        problem = create_problem()

        # User 1 creates interaction
        api_client.force_authenticate(user=user1)
        hint_url = reverse('coaching-hint')
        api_client.post(hint_url, {'problem_id': problem.id, 'student_code': 'def user1_code(): pass'})

        # User 2 checks history
        api_client.force_authenticate(user=user2)
        history_url = reverse('coaching-history', kwargs={'problem_id': problem.id})
        response = api_client.get(history_url)

        assert response.status_code == 200
        data = response.json()
        # Should be empty for user 2
        assert len(data) == 0

    def test_challenge_interaction_is_stored(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        url = reverse('coaching-challenge')
        payload = {'problem_id': problem.id, 'student_code': 'def twoSum(): pass', 'user_answer': 'Time complexity is O(N)'}
        response = api_client.post(url, payload)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'challenge' in data

        interaction = CoachingInteraction.objects.filter(user=user, problem=problem, interaction_type='challenge').first()
        assert interaction is not None
        assert interaction.user_question == 'Time complexity is O(N)'

    def test_feedback_interaction_is_stored(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        url = reverse('coaching-feedback')
        payload = {'problem_id': problem.id, 'student_code': 'def twoSum(): pass'}
        response = api_client.post(url, payload)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'feedback' in data
        assert 'approach' in data['feedback']

        interaction = CoachingInteraction.objects.filter(user=user, problem=problem, interaction_type='feedback').first()
        assert interaction is not None

    def test_ai_provider_failure_is_handled(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        with patch('apps.coaching.providers.mock.MockAIProvider.generate_hint', side_effect=Exception("API Network Timeout")):
            url = reverse('coaching-hint')
            response = api_client.post(url, {'problem_id': problem.id, 'student_code': 'def twoSum(): pass'})
            assert response.status_code == 200
            data = response.json()
            assert "AI Coach is temporarily unavailable" in data['hint']

    def test_invalid_ai_response_is_handled(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        with patch('apps.coaching.providers.mock.MockAIProvider.generate_hint', return_value=""):
            url = reverse('coaching-hint')
            response = api_client.post(url, {'problem_id': problem.id, 'student_code': 'def twoSum(): pass'})
            assert response.status_code == 200
            data = response.json()
            assert data['hint'] != ""

    def test_coaching_jsonl_export_works(self, create_user, create_problem, tmp_path):
        user = create_user()
        problem = create_problem()

        CoachingInteraction.objects.create(
            user=user,
            problem=problem,
            session_id=f"session_{user.id}_{problem.id}",
            student_code="def twoSum(): pass",
            hint_level=1,
            ai_response="Think about hash maps",
            interaction_type='hint'
        )

        output_file = tmp_path / "dataset.jsonl"
        call_command('export_coaching_dataset', output=str(output_file))

        assert output_file.exists()
        lines = output_file.read_text(encoding='utf-8').strip().split('\n')
        assert len(lines) == 1

        record = json.loads(lines[0])
        assert record['user_id'] == user.id
        assert record['problem']['id'] == problem.id
        assert record['hint_level'] == 1
        assert record['interaction_type'] == 'hint'
