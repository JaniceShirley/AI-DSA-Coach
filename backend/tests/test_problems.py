import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.problems.models import Problem

@pytest.mark.django_db
class TestProblemsAPI:
    def setup_method(self):
        self.client = APIClient()
        self.problem1 = Problem.objects.create(
            title="Two Sum",
            slug="two-sum",
            difficulty="Easy",
            topics=["Array", "Hash Table"],
            patterns=["Hash Map"],
            description="Find two sum indices",
            constraints=["2 <= len <= 1000"],
            examples=[{"input": "[2,7], 9", "output": "[0,1]"}],
            starter_code={"python": "def twoSum(): pass"}
        )
        self.problem2 = Problem.objects.create(
            title="Course Schedule",
            slug="course-schedule",
            difficulty="Medium",
            topics=["Graphs", "Topological Sort"],
            patterns=["Cycle Detection"],
            description="Can finish courses",
            constraints=["1 <= numCourses <= 2000"],
            examples=[{"input": "2, [[1,0]]", "output": "true"}],
            starter_code={"python": "def canFinish(): pass"}
        )

    def test_list_problems(self):
        url = reverse('problem-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_filter_problems_by_difficulty(self):
        url = reverse('problem-list')
        response = self.client.get(url, {'difficulty': 'Easy'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['slug'] == 'two-sum'

    def test_search_problems(self):
        url = reverse('problem-list')
        response = self.client.get(url, {'search': 'Schedule'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['slug'] == 'course-schedule'

    def test_get_problem_detail(self):
        url = reverse('problem-detail', kwargs={'slug': 'two-sum'})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Two Sum'
        assert response.data['difficulty'] == 'Easy'

    def test_get_problem_detail_not_found(self):
        url = reverse('problem-detail', kwargs={'slug': 'non-existent-problem'})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
