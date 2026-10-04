import pytest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.problems.models import Problem
from apps.submissions.models import Submission
from apps.interviews.models import InterviewSession, InterviewMessage, InterviewEvaluation

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user():
    def _user(email="candidate@example.com", password="password123"):
        return User.objects.create_user(email=email, password=password)
    return _user

@pytest.fixture
def create_problem():
    def _problem(title="Two Sum", slug="two-sum", difficulty="Easy", topics=None):
        if topics is None:
            topics = ["Hash Table", "Array"]
        return Problem.objects.create(
            title=title,
            slug=slug,
            description="Given an array of integers nums and an integer target, return indices of the two numbers.",
            difficulty=difficulty,
            topics=topics,
            patterns=["Two Pointers"],
            starter_code={"python": "def twoSum(nums, target):\n    pass"}
        )
    return _problem

@pytest.mark.django_db
class TestInterviewSystem:

    def test_unauthenticated_user_cannot_start_interview(self, api_client):
        url = reverse('interview-start')
        response = api_client.post(url, {'difficulty': 'Easy'})
        assert response.status_code == 401

    def test_authenticated_user_can_start_interview(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        url = reverse('interview-start')
        response = api_client.post(url, {'difficulty': 'Easy', 'problem_id': problem.id})

        assert response.status_code == 201
        data = response.json()
        assert 'session_id' in data
        assert data['status'] == 'IN_PROGRESS'
        assert 'message' in data
        assert data['problem']['id'] == problem.id

        session = InterviewSession.objects.get(id=data['session_id'])
        assert session.user == user
        assert session.messages.count() == 1
        assert session.messages.first().role == 'AI_INTERVIEWER'

    def test_user_can_respond_to_own_interview(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        start_res = api_client.post(reverse('interview-start'), {'problem_id': problem.id}).json()
        session_id = start_res['session_id']

        respond_url = reverse('interview-respond', kwargs={'session_id': session_id})
        response = api_client.post(respond_url, {'message': 'I would use a hash map to achieve O(N) time complexity.'})

        assert response.status_code == 200
        data = response.json()
        assert data['session_id'] == session_id
        assert 'message' in data
        assert 'stage' in data

        session = InterviewSession.objects.get(id=session_id)
        assert session.messages.count() >= 3 # 1 initial + 1 student + 1 AI follow-up

    def test_user_cannot_access_another_user_interview(self, api_client, create_user, create_problem):
        user1 = create_user(email="user1@example.com")
        user2 = create_user(email="user2@example.com")
        problem = create_problem()

        # User 1 starts interview
        api_client.force_authenticate(user=user1)
        start_res = api_client.post(reverse('interview-start'), {'problem_id': problem.id}).json()
        session_id = start_res['session_id']

        # User 2 tries to access User 1's interview
        api_client.force_authenticate(user=user2)
        detail_url = reverse('interview-detail', kwargs={'session_id': session_id})
        detail_res = api_client.get(detail_url)
        assert detail_res.status_code == 404

        respond_url = reverse('interview-respond', kwargs={'session_id': session_id})
        respond_res = api_client.post(respond_url, {'message': 'Hacking session'})
        assert respond_res.status_code == 404

    def test_stage_transitions_work(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        start_res = api_client.post(reverse('interview-start'), {'problem_id': problem.id}).json()
        session_id = start_res['session_id']
        respond_url = reverse('interview-respond', kwargs={'session_id': session_id})

        # Approach response -> should move to COMPLEXITY
        res1 = api_client.post(respond_url, {'message': 'I plan to use a dictionary for lookups.'}).json()
        assert res1['stage'] == 'COMPLEXITY'

        # Complexity response -> should move to EDGE_CASES
        res2 = api_client.post(respond_url, {'message': 'Time complexity is O(N) and space complexity is O(N).'}).json()
        assert res2['stage'] == 'EDGE_CASES'

    def test_interview_messages_are_stored(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        start_res = api_client.post(reverse('interview-start'), {'problem_id': problem.id}).json()
        session_id = start_res['session_id']

        api_client.post(reverse('interview-respond', kwargs={'session_id': session_id}), {'message': 'My proposed algorithm.'})

        messages = InterviewMessage.objects.filter(interview_session_id=session_id).order_by('created_at')
        assert messages.count() >= 3
        roles = [m.role for m in messages]
        assert 'AI_INTERVIEWER' in roles
        assert 'STUDENT' in roles

    def test_ai_failure_is_handled(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        start_res = api_client.post(reverse('interview-start'), {'problem_id': problem.id}).json()
        session_id = start_res['session_id']

        with patch('apps.coaching.providers.mock.MockAIProvider.conduct_interview_turn', side_effect=Exception("LLM Timeout")):
            respond_url = reverse('interview-respond', kwargs={'session_id': session_id})
            response = api_client.post(respond_url, {'message': 'Test message during outage'})
            assert response.status_code == 200
            data = response.json()
            assert 'message' in data

    def test_interview_can_be_completed(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        start_res = api_client.post(reverse('interview-start'), {'problem_id': problem.id}).json()
        session_id = start_res['session_id']

        end_url = reverse('interview-end', kwargs={'session_id': session_id})
        response = api_client.post(end_url)

        assert response.status_code == 200
        data = response.json()
        assert 'overall_score' in data
        assert 'strengths' in data
        assert 'areas_for_improvement' in data

        session = InterviewSession.objects.get(id=session_id)
        assert session.status == 'COMPLETED'
        assert session.completed_at is not None

    def test_evaluation_is_generated(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        start_res = api_client.post(reverse('interview-start'), {'problem_id': problem.id}).json()
        session_id = start_res['session_id']

        api_client.post(reverse('interview-end', kwargs={'session_id': session_id}))

        feedback_url = reverse('interview-feedback', kwargs={'session_id': session_id})
        response = api_client.get(feedback_url)

        assert response.status_code == 200
        data = response.json()
        assert data['overall_score'] >= 0
        assert 'problem_understanding' in data
        assert 'approach_quality' in data
        assert 'technical_reasoning' in data
        assert 'complexity_analysis' in data
        assert 'edge_case_awareness' in data

    def test_interview_history_works(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        api_client.post(reverse('interview-start'), {'problem_id': problem.id})
        api_client.post(reverse('interview-start'), {'problem_id': problem.id})

        list_url = reverse('interview-list')
        response = api_client.get(list_url)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_coding_submission_can_be_associated_with_interview(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        start_res = api_client.post(reverse('interview-start'), {'problem_id': problem.id}).json()
        session_id = start_res['session_id']

        submission = Submission.objects.create(
            user=user,
            problem=problem,
            code="def twoSum(nums, target): return [0, 1]",
            language="python",
            status="ACCEPTED",
            runtime=15.0,
            memory=12.5,
            test_cases_passed=5,
            total_test_cases=5
        )

        code_url = reverse('interview-code', kwargs={'session_id': session_id})
        response = api_client.post(code_url, {'submission_id': submission.id})

        assert response.status_code == 200
        data = response.json()
        assert data['submission_status'] == 'ACCEPTED'
        assert data['stage'] == 'CODING'

        session = InterviewSession.objects.get(id=session_id)
        assert session.submission == submission

    def test_recommendations_use_interview_results(self, api_client, create_user, create_problem):
        user = create_user()
        problem1 = create_problem(title="Problem One", slug="prob-1", topics=["Trees", "Binary Tree"])
        problem2 = create_problem(title="Problem Two", slug="prob-2", topics=["Graph", "DFS"])
        api_client.force_authenticate(user=user)

        session = InterviewSession.objects.create(
            user=user,
            problem=problem1,
            status='COMPLETED'
        )
        InterviewEvaluation.objects.create(
            interview_session=session,
            overall_score=75,
            recommended_topics=["Graph", "DFS"]
        )

        dash_url = reverse('dashboard-progress')
        response = api_client.get(dash_url)

        assert response.status_code == 200
        data = response.json()
        assert data['recommended_problem'] is not None
        # Recommended problem should prioritize Graph/DFS from evaluation
        assert "Graph" in data['recommended_problem']['topics']

    def test_speech_normalizer_handles_garbled_dsa_terms(self):
        from apps.interviews.speech_normalizer import normalize_dsa_transcript

        # Raw misrecognized speech example from user report:
        garbled = "I will first use the you know what root force approach that is I will hydrate from I will use root froze approach"
        normalized = normalize_dsa_transcript(garbled)

        assert "brute force" in normalized
        assert "root force" not in normalized
        assert "iterate through" in normalized
        assert "hydrate from" not in normalized

        # Complexity terms
        comp_raw = "It takes oh of n square time and oh of one space complexity"
        comp_norm = normalize_dsa_transcript(comp_raw)
        assert "O(n²)" in comp_norm
        assert "O(1)" in comp_norm

        # Preserves candidate errors and does not invent solutions
        mistake = "I'll use two pointer on an unsorted array"
        mistake_norm = normalize_dsa_transcript(mistake)
        assert "two pointers" in mistake_norm
        assert "unsorted array" in mistake_norm
        assert "hash map" not in mistake_norm  # MUST NOT rewrite to correct answer

    def test_interviewer_two_sum_turn_progression_and_no_echo(self, api_client, create_user, create_problem):
        user = create_user()
        problem = create_problem()
        api_client.force_authenticate(user=user)

        start_res = api_client.post(reverse('interview-start'), {'problem_id': problem.id}).json()
        session_id = start_res['session_id']
        respond_url = reverse('interview-respond', kwargs={'session_id': session_id})

        # Turn 1: Candidate proposes brute force with misrecognized words
        t1 = api_client.post(respond_url, {'message': "I will use root force and hydrate from every pair"}).json()
        assert t1['stage'] == 'COMPLEXITY'
        # Crucial requirement: No raw echoing like "I see your point regarding: ..."
        assert "I see your point regarding" not in t1['message']
        assert "hydrate from" not in t1['message']
        assert "time" in t1['message'].lower() or "complexity" in t1['message'].lower()

        # Turn 2: Candidate provides complexity
        t2 = api_client.post(respond_url, {'message': "It is oh of n square time and oh of one space"}).json()
        assert t2['stage'] == 'OPTIMIZATION'
        assert "O(n²)" in t2['message'] or "improve" in t2['message'].lower() or "optimize" in t2['message'].lower()

        # Turn 3: Candidate proposes two pointers on unsorted array (mistake)
        t3 = api_client.post(respond_url, {'message': "I can use two pointers on the unsorted array"}).json()
        # Should challenge the candidate and NOT jump stage to CODING or pretend it's a hash map
        assert "sorted" in t3['message'].lower()
        assert "unsorted" in t3['message'].lower()

        # Turn 4: Candidate proposes hash map
        t4 = api_client.post(respond_url, {'message': "Instead I will use a hash map to find the complement"}).json()
        assert "complement" in t4['message'].lower() or "hash map" in t4['message'].lower()

