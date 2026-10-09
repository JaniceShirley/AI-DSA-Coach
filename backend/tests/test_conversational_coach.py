import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from apps.problems.models import Problem, TestCase
from apps.coaching.models import CoachingSession, CoachingInteraction

User = get_user_model()

@pytest.mark.django_db
class TestConversationalDSACoach:
    def setup_method(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='student1@example.com',
            name='Student One',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            email='student2@example.com',
            name='Student Two',
            password='password123'
        )

        self.problem = Problem.objects.create(
            title="Contains Duplicate",
            slug="contains-duplicate-test",
            difficulty="Easy",
            topics=["Array", "Hash Table"],
            patterns=["Hash Set"],
            description="Given an integer array nums, return true if any value appears at least twice in the array, and return false if every element is distinct.",
            starter_code={"python": "def containsDuplicate(nums):\n    pass"}
        )

        # Test cases for Contains Duplicate
        self.tc1 = TestCase.objects.create(
            problem=self.problem,
            input_data="nums = [1, 2, 3, 1]",
            expected_output="True",
            is_public=True
        )
        self.tc2 = TestCase.objects.create(
            problem=self.problem,
            input_data="nums = [1, 2, 3, 4]",
            expected_output="False",
            is_public=True
        )

    # -------------------------------------------------------------------------
    # TEST A: Valid brute-force approach
    # Student proposes nested comparisons for Contains Duplicate.
    # Expected: The AI helps implement brute force without immediately redirecting to set.
    # -------------------------------------------------------------------------
    def test_scenario_a_valid_brute_force_approach(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('coaching-chat')
        data = {
            'problem_id': self.problem.id,
            'message': "I think I can use brute force with nested loops to compare every pair of elements.",
            'student_code': "def containsDuplicate(nums):\n    pass"
        }
        res = self.client.post(url, data, format='json')
        assert res.status_code == status.HTTP_200_OK
        resp_msg = res.data['message'].lower()
        # Verifies valid approach accepted and guided without immediately redirecting to set
        assert "valid approach" in resp_msg or "brute force" in resp_msg
        assert "nested" in resp_msg or "compare" in resp_msg
        assert res.data['current_approach']['type'] == 'brute_force'
        assert res.data['stage'] == 'GUIDED_IMPLEMENTATION'
        # Crucial: Must NOT reject or immediately force set-based solution
        assert "not valid" not in resp_msg

    # -------------------------------------------------------------------------
    # TEST B: Valid sorting approach
    # Student proposes sorting and checking adjacent elements.
    # Expected: The AI recognizes this as a valid approach and helps complete it.
    # -------------------------------------------------------------------------
    def test_scenario_b_valid_sorting_approach(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('coaching-chat')
        data = {
            'problem_id': self.problem.id,
            'message': "What if I sort the array first and check adjacent elements?",
            'student_code': ""
        }
        res = self.client.post(url, data, format='json')
        assert res.status_code == status.HTTP_200_OK
        resp_msg = res.data['message'].lower()
        assert "valid approach" in resp_msg or "sorting" in resp_msg
        assert res.data['current_approach']['type'] == 'sorting'
        assert res.data['stage'] == 'GUIDED_IMPLEMENTATION'

    # -------------------------------------------------------------------------
    # TEST C: Valid set-based approach
    # Student proposes using a set.
    # Expected: The AI guides implementation without immediately revealing complete code.
    # -------------------------------------------------------------------------
    def test_scenario_c_valid_set_based_approach(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('coaching-chat')
        data = {
            'problem_id': self.problem.id,
            'message': "Can I use a hash set to store seen numbers as I iterate?",
            'student_code': ""
        }
        res = self.client.post(url, data, format='json')
        assert res.status_code == status.HTTP_200_OK
        resp_msg = res.data['message'].lower()
        assert "valid approach" in resp_msg or "hash set" in resp_msg or "set" in resp_msg
        assert res.data['current_approach']['type'] == 'hash_set'
        # Must not dump complete runnable function solution
        assert "def containsduplicate" not in resp_msg

    # -------------------------------------------------------------------------
    # TEST D: Incorrect reasoning
    # Student proposes checking only first and last elements.
    # Expected: The AI uses a counterexample to help identify the issue.
    # -------------------------------------------------------------------------
    def test_scenario_d_incorrect_reasoning_counterexample(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('coaching-chat')
        data = {
            'problem_id': self.problem.id,
            'message': "Can I just check the first and last elements to see if there is a duplicate?",
            'student_code': ""
        }
        res = self.client.post(url, data, format='json')
        assert res.status_code == status.HTTP_200_OK
        resp_msg = res.data['message'].lower()
        # Must provide a counterexample or point out elements in the middle
        assert "counterexample" in resp_msg or "middle" in resp_msg or "[1, 2, 2, 4]" in resp_msg or "1" in resp_msg
        assert "first" in resp_msg and "last" in resp_msg
        assert res.data['stage'] == 'APPROACH_DISCOVERY'

    # -------------------------------------------------------------------------
    # TEST E: Incorrect implementation
    # Student chooses valid approach but writes code with a bug.
    # Expected: The AI identifies the implementation problem rather than rejecting the approach.
    # -------------------------------------------------------------------------
    def test_scenario_e_incorrect_implementation_isolated_bug(self):
        self.client.force_authenticate(user=self.user1)
        # Establish brute force approach
        url = reverse('coaching-chat')
        self.client.post(url, {
            'problem_id': self.problem.id,
            'message': "I am using brute force with nested loops.",
        }, format='json')

        # Buggy code: always returns None or missing return False
        buggy_code = (
            "def containsDuplicate(nums):\n"
            "    for i in range(len(nums)):\n"
            "        for j in range(i + 1, len(nums)):\n"
            "            if nums[i] == nums[j]:\n"
            "                return True\n"
        )
        res = self.client.post(url, {
            'problem_id': self.problem.id,
            'message': "Why is my code failing?",
            'student_code': buggy_code,
            'run_code': True
        }, format='json')

        assert res.status_code == status.HTTP_200_OK
        resp_msg = res.data['message'].lower()
        # Identifies the implementation issue (e.g. return False / default return) rather than rejecting brute force
        assert "return" in resp_msg or "bug" in resp_msg or "false" in resp_msg
        assert res.data['solution_status'] == 'INCORRECT'

    # -------------------------------------------------------------------------
    # TEST F: Correct but inefficient solution
    # The brute-force solution passes the relevant tests.
    # Expected: AI guides student through complexity analysis before encouraging optimization.
    # -------------------------------------------------------------------------
    def test_scenario_f_correct_inefficient_solution_guides_complexity(self):
        self.client.force_authenticate(user=self.user1)
        # Establish brute force approach
        url = reverse('coaching-chat')
        self.client.post(url, {
            'problem_id': self.problem.id,
            'message': "I am using brute force nested loops.",
        }, format='json')

        # Working brute force code
        correct_brute_force = (
            "def containsDuplicate(nums):\n"
            "    for i in range(len(nums)):\n"
            "        for j in range(i + 1, len(nums)):\n"
            "            if nums[i] == nums[j]:\n"
            "                return True\n"
            "    return False\n"
        )
        res = self.client.post(url, {
            'problem_id': self.problem.id,
            'message': "I wrote the brute force solution, please verify it.",
            'student_code': correct_brute_force,
            'run_code': True
        }, format='json')

        assert res.status_code == status.HTTP_200_OK
        resp_msg = res.data['message'].lower()
        assert res.data['solution_status'] == 'VERIFIED'
        assert res.data['stage'] == 'COMPLEXITY_ANALYSIS'
        assert "passed" in resp_msg or "work" in resp_msg
        assert "complexity" in resp_msg

    # -------------------------------------------------------------------------
    # TEST G: Student discovers an optimization
    # The student suggests using a set after the complexity discussion.
    # Expected: AI recognizes the new approach and helps implement it.
    # -------------------------------------------------------------------------
    def test_scenario_g_student_discovers_optimization(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('coaching-chat')
        # Simulate being in OPTIMIZATION_DISCOVERY
        session = CoachingSession.objects.create(
            user=self.user1,
            problem=self.problem,
            stage='OPTIMIZATION_DISCOVERY',
            current_approach={'name': 'Brute Force', 'type': 'brute_force'},
            explored_approaches=[{'name': 'Brute Force', 'type': 'brute_force', 'status': 'VERIFIED'}]
        )

        res = self.client.post(url, {
            'problem_id': self.problem.id,
            'message': "To optimize this, what if we use a hash set so we can lookup seen numbers in O(1) time?",
            'student_code': ""
        }, format='json')

        assert res.status_code == status.HTTP_200_OK
        resp_msg = res.data['message'].lower()
        assert "set" in resp_msg or "insight" in resp_msg or "hash" in resp_msg
        assert res.data['stage'] == 'OPTIMIZED_IMPLEMENTATION'
        assert res.data['current_approach']['type'] == 'hash_set'

    # -------------------------------------------------------------------------
    # TEST H: Wrong complexity estimate
    # Student incorrectly estimates time complexity (e.g. says nested loops is O(N)).
    # Expected: AI offers a small explanatory clue and helps correct it.
    # -------------------------------------------------------------------------
    def test_scenario_h_wrong_complexity_estimate(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('coaching-chat')
        session = CoachingSession.objects.create(
            user=self.user1,
            problem=self.problem,
            stage='COMPLEXITY_ANALYSIS',
            current_approach={'name': 'Brute Force', 'type': 'brute_force'},
            solution_status='VERIFIED'
        )

        res = self.client.post(url, {
            'problem_id': self.problem.id,
            'message': "I think the time complexity of the nested loops is O(N).",
            'student_code': ""
        }, format='json')

        assert res.status_code == status.HTTP_200_OK
        resp_msg = res.data['message'].lower()
        # Offers explanation of outer loop vs inner loop
        assert "trace" in resp_msg or "loop" in resp_msg or "comparisons" in resp_msg
        assert res.data['stage'] == 'COMPLEXITY_ANALYSIS'

    # -------------------------------------------------------------------------
    # TEST I: Student gets stuck
    # Student repeatedly says they do not understand / are stuck.
    # Expected: AI simplifies explanation and provides more specific guidance without dumping solution.
    # -------------------------------------------------------------------------
    def test_scenario_i_student_gets_stuck_simplification(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('coaching-chat')

        # First stuck
        res1 = self.client.post(url, {
            'problem_id': self.problem.id,
            'message': "I am stuck and I don't understand how to start.",
        }, format='json')
        assert res1.status_code == status.HTTP_200_OK
        assert "def containsduplicate" not in res1.data['message'].lower()

        # Repeated stuck
        res2 = self.client.post(url, {
            'problem_id': self.problem.id,
            'message': "I'm still stuck and confused.",
        }, format='json')
        assert res2.status_code == status.HTTP_200_OK
        resp_msg2 = res2.data['message'].lower()
        # Provides concrete example clue
        assert "simplest" in resp_msg2 or "loop" in resp_msg2 or "compare" in resp_msg2
        assert "def containsduplicate" not in resp_msg2

    # -------------------------------------------------------------------------
    # TEST J: Context retention
    # Student refers to an approach discussed earlier.
    # Expected: The AI retains context and session state across turns.
    # -------------------------------------------------------------------------
    def test_scenario_j_context_retention(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('coaching-chat')

        # Turn 1: Propose sorting
        self.client.post(url, {
            'problem_id': self.problem.id,
            'message': "I want to use sorting for this problem.",
        }, format='json')

        # Turn 2: Follow-up question referencing sorting
        res = self.client.post(url, {
            'problem_id': self.problem.id,
            'message': "After doing the sorting step, how do adjacent elements help?",
        }, format='json')

        assert res.status_code == status.HTTP_200_OK
        session_res = self.client.get(reverse('coaching-session-state', kwargs={'problem_id': self.problem.id}))
        assert session_res.data['current_approach']['type'] == 'sorting'
        assert len(session_res.data['messages']) >= 4

    # -------------------------------------------------------------------------
    # TEST K: No fabricated results
    # The AI must not claim code passed tests without actual execution evidence.
    # -------------------------------------------------------------------------
    def test_scenario_k_no_fabricated_results(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('coaching-chat')

        # Empty code review
        res = self.client.post(url, {
            'problem_id': self.problem.id,
            'message': "Did my code pass the tests?",
            'student_code': "",
            'run_code': True
        }, format='json')
        assert res.status_code == status.HTTP_200_OK
        assert "passed all" not in res.data['message'].lower()
        assert res.data['solution_status'] == 'IN_PROGRESS'

    # -------------------------------------------------------------------------
    # TEST L: Authentication and isolation
    # User 2 cannot access User 1's coaching sessions or history.
    # -------------------------------------------------------------------------
    def test_scenario_l_authentication_and_user_isolation(self):
        # User 1 creates session and chat
        self.client.force_authenticate(user=self.user1)
        url = reverse('coaching-chat')
        self.client.post(url, {
            'problem_id': self.problem.id,
            'message': "User 1 private approach message.",
        }, format='json')

        # User 2 queries their session for the same problem
        self.client.force_authenticate(user=self.user2)
        session_url = reverse('coaching-session-state', kwargs={'problem_id': self.problem.id})
        res2 = self.client.get(session_url)
        assert res2.status_code == status.HTTP_200_OK
        # User 2's session must be isolated and empty, NOT containing User 1's messages
        user2_messages = [m['content'] for m in res2.data['messages']]
        assert "User 1 private approach message." not in user2_messages

        # Unauthenticated request is rejected
        self.client.logout()
        res_unauth = self.client.get(session_url)
        assert res_unauth.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    # -------------------------------------------------------------------------
    # TEST M: Alternative valid approaches
    # Approach not in fixed catalogue (e.g. bit manipulation or custom data structure).
    # Expected: The AI reasons about it instead of rejecting solely because unfamiliar.
    # -------------------------------------------------------------------------
    def test_scenario_m_alternative_valid_approaches(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('coaching-chat')
        data = {
            'problem_id': self.problem.id,
            'message': "Can I use bit manipulation or a frequency array to solve this?",
            'student_code': ""
        }
        res = self.client.post(url, data, format='json')
        assert res.status_code == status.HTTP_200_OK
        resp_msg = res.data['message'].lower()
        # Recognizes technique and does not outright reject
        assert "bit manipulation" in resp_msg or "frequency array" in resp_msg or "intriguing" in resp_msg or "strategy" in resp_msg
        assert "not allowed" not in resp_msg
