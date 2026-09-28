import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from apps.problems.models import Problem, TestCase
from apps.progress.models import UserProblemProgress
from apps.submissions.models import Submission

User = get_user_model()

@pytest.mark.django_db
class TestPhase3SubmissionsAndAnalytics:
    def setup_method(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1_phase3@example.com',
            name='Phase3 User One',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            email='user2_phase3@example.com',
            name='Phase3 User Two',
            password='password123'
        )

        self.problem = Problem.objects.create(
            title="Two Sum",
            slug="two-sum-phase3",
            difficulty="Easy",
            topics=["Array", "Hash Table"],
            patterns=["Hash Map"],
            description="Given nums and target...",
            starter_code={"python": "def twoSum(nums, target):\n    return [0, 1]"}
        )

        # Create TestCases
        self.tc1 = TestCase.objects.create(
            problem=self.problem,
            input_data="nums = [2,7,11,15]\ntarget = 9",
            expected_output="[0, 1]",
            is_public=True
        )
        self.tc2 = TestCase.objects.create(
            problem=self.problem,
            input_data="nums = [3,2,4]\ntarget = 6",
            expected_output="[1, 2]",
            is_public=False
        )

    def test_run_code_public_test_cases(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('submission-run')
        data = {
            'problem_id': self.problem.id,
            'code': "def twoSum(nums, target):\n    return [0, 1]",
            'language': 'python'
        }
        response = self.client.post(url, data, format='json')
        print("\nDEBUG RUN RESPONSE:", response.data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'ACCEPTED'
        assert response.data['test_cases_passed'] == 1
        assert response.data['total_test_cases'] == 1 # Public testcases only

    def test_submit_code_accepted_updates_progress_to_solved(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('submission-submit')
        # Correct code for both testcases
        code = "def twoSum(nums, target):\n    if nums == [2,7,11,15]: return [0,1]\n    return [1,2]"
        data = {
            'problem_id': self.problem.id,
            'code': code,
            'language': 'python'
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'ACCEPTED'
        assert response.data['test_cases_passed'] == 2
        assert response.data['total_test_cases'] == 2

        # Verify submission saved in DB
        assert Submission.objects.filter(user=self.user1, problem=self.problem).exists()

        # Verify progress updated to SOLVED
        progress = UserProblemProgress.objects.get(user=self.user1, problem=self.problem)
        assert progress.status == 'SOLVED'
        assert progress.attempts == 1
        assert progress.solved_at is not None

    def test_submit_code_wrong_answer_updates_progress_to_attempted(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('submission-submit')
        code = "def twoSum(nums, target):\n    return [99, 99]" # Wrong answer
        data = {
            'problem_id': self.problem.id,
            'code': code,
            'language': 'python'
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'WRONG_ANSWER'

        # Verify progress updated to ATTEMPTED
        progress = UserProblemProgress.objects.get(user=self.user1, problem=self.problem)
        assert progress.status == 'ATTEMPTED'
        assert progress.attempts == 1
        assert progress.solved_at is None

    def test_submission_user_isolation(self):
        # User 1 submits solution
        Submission.objects.create(
            user=self.user1,
            problem=self.problem,
            code="pass",
            language="python",
            status="ACCEPTED",
            test_cases_passed=2,
            total_test_cases=2
        )

        # User 2 checks submission list
        self.client.force_authenticate(user=self.user2)
        url = reverse('submission-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0 # User 2 cannot see User 1's submission

    def test_analytics_api_endpoint(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('analytics-dashboard')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'total_problems' in response.data
        assert 'solved_count' in response.data
        assert 'solved_by_topic' in response.data
        assert 'recommended_problem' in response.data
