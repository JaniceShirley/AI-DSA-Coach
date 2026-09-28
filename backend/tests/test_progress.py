import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from apps.problems.models import Problem
from apps.progress.models import UserProblemProgress

User = get_user_model()

@pytest.mark.django_db
class TestProgressAPI:
    def setup_method(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            name='User One',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            name='User Two',
            password='password123'
        )
        self.problem = Problem.objects.create(
            title="Two Sum",
            slug="two-sum",
            difficulty="Easy",
            topics=["Array"],
            description="Two sum description",
            starter_code={"python": "pass"}
        )

    def test_dashboard_unauthenticated_fails(self):
        url = reverse('dashboard-progress')
        response = self.client.get(url)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_record_attempt_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('problem-progress-detail', kwargs={'problem_id': self.problem.id})
        data = {
            'status': 'SOLVED',
            'time_spent': 120,
            'code': 'def twoSum(nums, target): return [0, 1]'
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'SOLVED'
        assert response.data['attempts'] == 1
        assert response.data['time_spent'] == 120

    def test_user_isolation_progress(self):
        # User 1 solves problem
        UserProblemProgress.objects.create(
            user=self.user1,
            problem=self.problem,
            status='SOLVED',
            attempts=1
        )

        # User 2 checks dashboard
        self.client.force_authenticate(user=self.user2)
        url = reverse('dashboard-progress')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # User 2 has 0 solved problems despite User 1 solving it
        assert response.data['solved_count'] == 0
        assert response.data['attempted_count'] == 0
