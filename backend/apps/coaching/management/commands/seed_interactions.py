import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.problems.models import Problem
from apps.submissions.models import Submission
from apps.coaching.models import CoachingInteraction
from apps.interviews.models import InterviewSession, InterviewMessage, InterviewEvaluation

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds realistic AI coaching interactions, submissions, and mock interview sessions for Phase 6 dataset pipeline.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing interactions and interview sessions before seeding.'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write("Clearing existing coaching and interview records...")
            CoachingInteraction.objects.all().delete()
            InterviewMessage.objects.all().delete()
            InterviewEvaluation.objects.all().delete()
            InterviewSession.objects.all().delete()
            Submission.objects.all().delete()

        # Ensure seed users
        emails = [
            'alex.coder@example.com',
            'devon.algo@example.com',
            'sara.systems@example.com',
            'marcus.dsa@example.com',
            'elena.tech@example.com'
        ]
        users = []
        for email in emails:
            u, _ = User.objects.get_or_create(email=email, defaults={'name': email.split('@')[0].replace('.', ' ').title()})
            users.append(u)

        problems = list(Problem.objects.all())
        if not problems:
            self.stdout.write(self.style.ERROR("No problems found! Run 'python manage.py seed_problems' first."))
            return

        self.stdout.write(f"Found {len(problems)} problems and {len(users)} users.")

        interactions_count = 0
        interviews_count = 0

        # Detailed templates for realistic coaching
        seed_coaching_data = [
            {
                "slug": "two-sum",
                "student_code": "def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n    return []",
                "interactions": [
                    {
                        "type": "hint",
                        "hint_level": 1,
                        "question": "My solution is too slow for large arrays. How can I improve it?",
                        "response": "Notice how your nested loops take O(N^2) time by repeatedly scanning the rest of the array. For any given number `x`, what exact complementary value do you need to find, and how fast could you search for it?"
                    },
                    {
                        "type": "hint",
                        "hint_level": 2,
                        "question": "I know the complement is target - nums[i]. How do I look it up in O(1)?",
                        "response": "Consider using a Hash Map (dictionary in Python). As you iterate through the list, what would happen if you stored previously seen numbers and their indices?"
                    },
                    {
                        "type": "hint",
                        "hint_level": 3,
                        "question": "Should I put all numbers in the dictionary first or while looping?",
                        "response": "A single-pass hash table works best: for each element `nums[i]`, first check if `target - nums[i]` is already in your dictionary. If it is, you've found your pair! If not, store `nums[i]: i` and continue."
                    },
                    {
                        "type": "challenge",
                        "hint_level": None,
                        "question": "Can I solve Two Sum with two pointers if I sort the array first?",
                        "response": "Sorting allows a two-pointer approach in O(N log N) time and O(1) auxiliary space. However, this problem asks for the original *indices*. How would sorting affect the original indices, and how could you preserve them?"
                    },
                    {
                        "type": "alternative",
                        "hint_level": None,
                        "question": "What are the trade-offs between Hash Map and Two Pointers here?",
                        "response": "Hash Map achieves O(N) time at the cost of O(N) space. The Two-Pointer approach achieves O(1) extra space (if modifying input is allowed) but takes O(N log N) time to sort, and requires storing `(val, original_index)` pairs."
                    },
                    {
                        "type": "feedback",
                        "hint_level": None,
                        "question": "Is my brute force approach acceptable for interviews?",
                        "response": "Your brute force implementation correctly finds the solution in O(N^2) time and O(1) space. In an interview, mention this as your initial baseline, then immediately transition to the O(N) hash map optimization."
                    }
                ]
            },
            {
                "slug": "contains-duplicate",
                "student_code": "def containsDuplicate(nums):\n    s = set()\n    for n in nums:\n        if n in s:\n            return True\n        s.add(n)\n    return False",
                "interactions": [
                    {
                        "type": "hint",
                        "hint_level": 1,
                        "question": "Is there any edge case I might be missing?",
                        "response": "Consider constraints: what happens when `nums` has fewer than 2 elements, or when all elements are identical, or with negative numbers? Your hash set correctly handles all element values."
                    },
                    {
                        "type": "challenge",
                        "hint_level": None,
                        "question": "What if memory is extremely constrained and I cannot use O(N) extra space?",
                        "response": "If memory is tight, how could you identify duplicate adjacent values without a hash set? What if you sorted the array in-place first?"
                    },
                    {
                        "type": "feedback",
                        "hint_level": None,
                        "question": "How is my code quality and efficiency?",
                        "response": "Your solution is optimal: O(N) time complexity and O(N) worst-case space complexity with early exit upon detecting the first duplicate."
                    }
                ]
            },
            {
                "slug": "valid-anagram",
                "student_code": "def isAnagram(s, t):\n    return sorted(s) == sorted(t)",
                "interactions": [
                    {
                        "type": "hint",
                        "hint_level": 1,
                        "question": "Can I do better than sorting strings?",
                        "response": "Sorting takes O(N log N) time where N is the string length. Since an anagram is defined solely by character frequencies, what data structure can track character counts in O(N) time?"
                    },
                    {
                        "type": "hint",
                        "hint_level": 2,
                        "question": "Should I use collections.Counter or an array of size 26?",
                        "response": "Since the problem specifies lowercase English letters, a fixed array of size 26 gives strictly O(1) auxiliary space and cache-friendly operations. In Python, `collections.Counter` is also very idiomatic."
                    },
                    {
                        "type": "challenge",
                        "hint_level": None,
                        "question": "What if the inputs contain Unicode characters instead of just a-z?",
                        "response": "With arbitrary Unicode characters, a fixed 26-element array won't suffice because the character space is over a million codepoints. In that case, a dynamic Hash Map (like `dict` or `Counter`) scales proportionally to the number of distinct characters."
                    }
                ]
            },
            {
                "slug": "product-of-array-except-self",
                "student_code": "def productExceptSelf(nums):\n    total = 1\n    for x in nums: total *= x\n    return [total // x for x in nums]",
                "interactions": [
                    {
                        "type": "hint",
                        "hint_level": 1,
                        "question": "The problem says without using division. How can I compute products without division?",
                        "response": "Think of each element `answer[i]` as the product of everything to its left multiplied by everything to its right: `prefix_product[i-1] * suffix_product[i+1]`. How can you precalculate these?"
                    },
                    {
                        "type": "hint",
                        "hint_level": 2,
                        "question": "How can I achieve O(1) extra space complexity?",
                        "response": "Use the output array itself to accumulate prefix products in a first pass. Then, use a single rolling variable `postfix` to multiply suffix products from right to left in a second pass."
                    },
                    {
                        "type": "feedback",
                        "hint_level": None,
                        "question": "Why did my division solution fail on test case [0, 0]?",
                        "response": "Division by zero raises `ZeroDivisionError` whenever the input contains zeros. Furthermore, division was explicitly prohibited in the problem statement. The prefix/suffix product approach avoids both issues."
                    }
                ]
            },
            {
                "slug": "maximum-subarray",
                "student_code": "def maxSubArray(nums):\n    max_sum = nums[0]\n    for i in range(len(nums)):\n        curr = 0\n        for j in range(i, len(nums)):\n            curr += nums[j]\n            max_sum = max(max_sum, curr)\n    return max_sum",
                "interactions": [
                    {
                        "type": "hint",
                        "hint_level": 1,
                        "question": "How can I avoid recalculating subarrays in O(N^2)?",
                        "response": "Kadane's algorithm asks a key question at each index `i`: is it better to extend the existing subarray sum (`curr_sum + nums[i]`), or restart fresh from `nums[i]`?"
                    },
                    {
                        "type": "hint",
                        "hint_level": 2,
                        "question": "What if all numbers in the array are negative?",
                        "response": "If all numbers are negative, the maximum subarray is simply the least negative single element. If you initialize `max_sum` to `nums[0]` (instead of `0`), your logic will naturally handle all-negative inputs."
                    },
                    {
                        "type": "challenge",
                        "hint_level": None,
                        "question": "Can this be solved using Divide and Conquer in O(N log N)?",
                        "response": "Yes! Split the array into halves. The maximum subarray either lies entirely in the left half, entirely in the right half, or crosses the midpoint. How would you calculate the crossing subarray sum in O(N)?"
                    }
                ]
            },
            {
                "slug": "valid-parentheses",
                "student_code": "def isValid(s):\n    stack = []\n    mapping = {')': '(', '}': '{', ']': '['}\n    for char in s:\n        if char in mapping:\n            top = stack.pop() if stack else '#'\n            if mapping[char] != top:\n                return False\n        else:\n            stack.append(char)\n    return len(stack) == 0",
                "interactions": [
                    {
                        "type": "hint",
                        "hint_level": 1,
                        "question": "Is a stack the only way to solve this?",
                        "response": "Because parentheses follow a Last-In, First-Out (LIFO) nesting structure, a stack is the natural and optimal O(N) time and O(N) space data structure."
                    },
                    {
                        "type": "feedback",
                        "hint_level": None,
                        "question": "What are common pitfalls with parentheses problems?",
                        "response": "Common pitfalls include forgetting to check if the stack is empty before popping (leading to IndexError), and forgetting to check `len(stack) == 0` at the end (e.g. string with only opening brackets like `'((('`). Your code handles both correctly!"
                    }
                ]
            },
            {
                "slug": "merge-two-sorted-lists",
                "student_code": "def mergeTwoLists(list1, list2):\n    dummy = ListNode(0)\n    curr = dummy\n    while list1 and list2:\n        if list1.val < list2.val:\n            curr.next = list1\n            list1 = list1.next\n        else:\n            curr.next = list2\n            list2 = list2.next\n        curr = curr.next\n    curr.next = list1 or list2\n    return dummy.next",
                "interactions": [
                    {
                        "type": "hint",
                        "hint_level": 1,
                        "question": "Why use a dummy node in linked list problems?",
                        "response": "A dummy head node eliminates edge-case conditionals for setting the initial head pointer, making list manipulation code cleaner and less error-prone."
                    },
                    {
                        "type": "alternative",
                        "hint_level": None,
                        "question": "Can this be implemented recursively?",
                        "response": "Yes, recursively: if not list1: return list2; if not list2: return list1. Pick the smaller node, set its `.next = mergeTwoLists(...)`, and return it. Notice that while it is elegant, recursion consumes O(N+M) call stack space compared to O(1) iteratively."
                    }
                ]
            },
            {
                "slug": "binary-search",
                "student_code": "def search(nums, target):\n    low, high = 0, len(nums) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if nums[mid] == target:\n            return mid\n        elif nums[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1",
                "interactions": [
                    {
                        "type": "challenge",
                        "hint_level": None,
                        "question": "In languages like Java or C++, what issue can `(low + high) // 2` cause?",
                        "response": "Integer overflow! If `low + high` exceeds the maximum 32-bit signed integer (`2^31 - 1`), it wraps to negative. The safe formula is `mid = low + (high - low) // 2`. In Python, integers have arbitrary precision, but mentioning this in interviews demonstrates deep systems awareness."
                    },
                    {
                        "type": "hint",
                        "hint_level": 2,
                        "question": "When should the loop condition be `low <= high` vs `low < high`?",
                        "response": "If your search space is inclusive `[low, high]`, use `while low <= high:` because when `low == high`, there is still one valid candidate element to inspect. If using half-open `[low, high)`, use `low < high`."
                    }
                ]
            }
        ]

        # Additional interactions across other seeded problems to ensure broad coverage
        for p in problems:
            # Check if problem already handled above
            if any(item['slug'] == p.slug for item in seed_coaching_data):
                continue

            user = random.choice(users)
            # Create a progressive hint sequence
            seed_coaching_data.append({
                "slug": p.slug,
                "student_code": p.starter_code.get("python", "def solution():\n    pass"),
                "interactions": [
                    {
                        "type": "hint",
                        "hint_level": 1,
                        "question": f"Where should I start on {p.title}?",
                        "response": f"Begin by clarifying inputs and constraints for {p.title}. What properties of the data structures involved ({', '.join(p.topics)}) can you leverage to break this problem into smaller sub-problems?"
                    },
                    {
                        "type": "hint",
                        "hint_level": 2,
                        "question": "What algorithmic pattern fits best?",
                        "response": f"For {p.title}, consider the '{p.patterns[0] if p.patterns else 'iterative'}' pattern. Ask yourself what state must be updated at each step to avoid redundant computation."
                    },
                    {
                        "type": "challenge",
                        "hint_level": None,
                        "question": "What is the primary trade-off in this approach?",
                        "response": f"Examine the space-time trade-off: can you reduce time complexity by allocating additional memory, or can the algorithm run in-place with O(1) auxiliary space?"
                    }
                ]
            })

        # Save coaching interactions
        for data in seed_coaching_data:
            problem = Problem.objects.filter(slug=data["slug"]).first()
            if not problem:
                continue

            user = random.choice(users)
            session_id = f"session_{user.id}_{problem.id}_{random.randint(1000, 9999)}"

            # Create a submission for reference
            sub = Submission.objects.create(
                user=user,
                problem=problem,
                code=data["student_code"],
                language="python",
                status="ACCEPTED" if "return" in data["student_code"] else "WRONG_ANSWER",
                runtime=28.5,
                memory=14.2,
                test_cases_passed=5,
                total_test_cases=5
            )

            for item in data["interactions"]:
                CoachingInteraction.objects.create(
                    user=user,
                    problem=problem,
                    session_id=session_id,
                    student_code=data["student_code"],
                    hint_level=item.get("hint_level"),
                    user_question=item.get("question"),
                    ai_response=item.get("response"),
                    interaction_type=item.get("type", "hint"),
                    submission=sub,
                    evaluation_metadata={
                        "relevance": 5,
                        "correctness": 5,
                        "hint_specificity": item.get("hint_level") or 2,
                        "solution_leakage": False,
                        "helpfulness": 5
                    }
                )
                interactions_count += 1

        # Intentionally inject test edge cases for data quality validation:
        # 1. Empty response
        prob_first = problems[0]
        u_first = users[0]
        CoachingInteraction.objects.create(
            user=u_first,
            problem=prob_first,
            session_id="session_invalid_empty",
            student_code="def broken(): pass",
            hint_level=1,
            user_question="Help me",
            ai_response="",
            interaction_type="hint"
        )
        interactions_count += 1

        # 2. Extremely short trivial response
        CoachingInteraction.objects.create(
            user=u_first,
            problem=prob_first,
            session_id="session_invalid_short",
            student_code="def broken(): pass",
            hint_level=1,
            user_question="Is this right?",
            ai_response="Ok.",
            interaction_type="hint"
        )
        interactions_count += 1

        # 3. Duplicate record
        dup_text = "Check if target - nums[i] is in your seen hash map."
        for _ in range(2):
            CoachingInteraction.objects.create(
                user=u_first,
                problem=prob_first,
                session_id="session_duplicate_test",
                student_code="def twoSum(nums, target): pass",
                hint_level=2,
                user_question="How does hash map lookup work?",
                ai_response=dup_text,
                interaction_type="hint"
            )
            interactions_count += 1

        # 4. Solution leakage record
        leak_code = (
            "Here is the complete solution:\n"
            "```python\n"
            "def twoSum(nums: list[int], target: int) -> list[int]:\n"
            "    seen = {}\n"
            "    for i, num in enumerate(nums):\n"
            "        diff = target - num\n"
            "        if diff in seen:\n"
            "            return [seen[diff], i]\n"
            "        seen[num] = i\n"
            "    return []\n"
            "```"
        )
        CoachingInteraction.objects.create(
            user=u_first,
            problem=prob_first,
            session_id="session_leakage_sample",
            student_code="def twoSum(): pass",
            hint_level=1,
            user_question="Give me the code",
            ai_response=leak_code,
            interaction_type="hint"
        )
        interactions_count += 1

        # Seed Mock Technical Interview Sessions
        interview_templates = [
            {
                "slug": "two-sum",
                "difficulty": "Easy",
                "dialogue": [
                    ("AI_INTERVIEWER", "PROBLEM_INTRO", "Welcome! Today we will work on 'Two Sum'. Given an array of integers and a target value, find indices of two numbers that add up to target. To start, how would you approach this problem?"),
                    ("STUDENT", "APPROACH", "A simple approach would be checking every pair with two nested loops. But that is O(N^2). We can do better with a hash map to look up the complement in O(1)."),
                    ("AI_INTERVIEWER", "COMPLEXITY", "Great observation! What would be the exact time and space complexity of that hash map approach?"),
                    ("STUDENT", "COMPLEXITY", "Time complexity would be O(N) because we iterate through the list once. Space complexity is O(N) in the worst case to store up to N elements in the hash map."),
                    ("AI_INTERVIEWER", "EDGE_CASES", "Spot on. What edge cases should we watch out for before writing code?"),
                    ("STUDENT", "EDGE_CASES", "We should consider arrays with negative numbers, duplicates that sum to target like [3, 3] with target 6, and ensure we don't use the exact same element twice."),
                    ("AI_INTERVIEWER", "CODING", "Excellent. Please go ahead and write the implementation."),
                    ("STUDENT", "CODING", "```python\ndef twoSum(nums: list[int], target: int) -> list[int]:\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []\n```"),
                    ("AI_INTERVIEWER", "FINAL_EVALUATION", "Fantastic job! Your solution is clean, optimal, and your complexity analysis and edge case awareness were thorough.")
                ],
                "evaluation": {
                    "overall_score": 92,
                    "problem_understanding": {"score": 95, "feedback": "Quickly grasped core constraints and immediately identified the complement requirement."},
                    "approach_quality": {"score": 90, "feedback": "Transitioned seamlessly from brute force to optimal one-pass hash map."},
                    "technical_reasoning": {"score": 92, "feedback": "Clear explanation of hash table lookup performance."},
                    "complexity_analysis": {"score": 95, "feedback": "Correctly analyzed O(N) time and O(N) space complexities."},
                    "edge_case_awareness": {"score": 90, "feedback": "Identified duplicate values and self-pairing edge cases."},
                    "optimization": {"score": 90, "feedback": "Used single-pass hash map instead of two-pass."},
                    "communication": {"score": 92, "feedback": "Clear, concise, and structured verbal delivery."},
                    "coding_correctness": {"score": 95, "feedback": "Bug-free implementation matching optimal algorithmic structure."},
                    "strengths": ["Rapid optimization from O(N^2) to O(N)", "Precise handling of identical values in map", "Clean Python idioms"],
                    "areas_for_improvement": ["Could mention space-saving two-pointer trade-off if input were sorted"],
                    "final_feedback": "Strong candidate demonstration of fundamentals and communication."
                }
            },
            {
                "slug": "valid-parentheses",
                "difficulty": "Easy",
                "dialogue": [
                    ("AI_INTERVIEWER", "PROBLEM_INTRO", "Let's explore 'Valid Parentheses'. Given a string with brackets '()[]{}', determine if the input string is valid. How would you structure this?"),
                    ("STUDENT", "APPROACH", "Because brackets must close in reverse order of how they opened, this has a LIFO property. I will use a stack. Push opening brackets, and for closing brackets, pop and check if it matches."),
                    ("AI_INTERVIEWER", "COMPLEXITY", "What are the time and space bounds for this stack approach?"),
                    ("STUDENT", "COMPLEXITY", "Time is O(N) where N is length of string since we process each character once. Space is O(N) for the stack in the worst case (e.g. all opening brackets)."),
                    ("AI_INTERVIEWER", "EDGE_CASES", "What happens if the string begins with a closing bracket, or has odd length?"),
                    ("STUDENT", "EDGE_CASES", "If length is odd, it's immediately False. If closing bracket appears when stack is empty, it's invalid."),
                    ("AI_INTERVIEWER", "FINAL_EVALUATION", "Well reasoned! Good instinct on early termination with odd string lengths.")
                ],
                "evaluation": {
                    "overall_score": 88,
                    "problem_understanding": {"score": 90, "feedback": "Identified LIFO stack mapping."},
                    "approach_quality": {"score": 88, "feedback": "Standard optimal stack mechanism."},
                    "technical_reasoning": {"score": 88, "feedback": "Sound reasoning on bracket matching."},
                    "complexity_analysis": {"score": 90, "feedback": "Accurate O(N) time/space analysis."},
                    "edge_case_awareness": {"score": 85, "feedback": "Good identification of odd lengths and empty stack pops."},
                    "optimization": {"score": 85, "feedback": "Early return for odd length was a nice touch."},
                    "communication": {"score": 90, "feedback": "Professional and crisp."},
                    "coding_correctness": {"score": 88, "feedback": "Solid structural design."},
                    "strengths": ["Recognized LIFO structure immediately", "Proactively handled empty stack corner case"],
                    "areas_for_improvement": ["Consider testing with mixed invalid nested types"],
                    "final_feedback": "Solid performance demonstrating competence with linear data structures."
                }
            },
            {
                "slug": "maximum-subarray",
                "difficulty": "Medium",
                "dialogue": [
                    ("AI_INTERVIEWER", "PROBLEM_INTRO", "We are looking at 'Maximum Subarray'. Find the contiguous subarray within an integer array that has the largest sum. What thoughts do you have?"),
                    ("STUDENT", "APPROACH", "We can solve this in O(N) time using Kadane's Algorithm. We maintain a current running sum and global max. If running sum drops below 0, we reset it."),
                    ("AI_INTERVIEWER", "COMPLEXITY", "Why does resetting to 0 when negative work? What if all elements in the array are negative?"),
                    ("STUDENT", "COMPLEXITY", "If running sum is negative, adding it to the next element only decreases that element's potential sum. If all elements are negative, resetting to 0 could return 0 incorrectly unless we track max element! So we should reset to current element instead: curr = max(num, curr + num)."),
                    ("AI_INTERVIEWER", "FINAL_EVALUATION", "Superb catch on the all-negative input case! That is the most common bug candidates make.")
                ],
                "evaluation": {
                    "overall_score": 94,
                    "problem_understanding": {"score": 95, "feedback": "Immediate grasp of contiguous subarray dynamics."},
                    "approach_quality": {"score": 95, "feedback": "Kadane's algorithm executed cleanly."},
                    "technical_reasoning": {"score": 96, "feedback": "Flawlessly explained why negative prefixes are discarded."},
                    "complexity_analysis": {"score": 95, "feedback": "O(N) time and O(1) space."},
                    "edge_case_awareness": {"score": 92, "feedback": "Self-corrected on all-negative arrays."},
                    "optimization": {"score": 95, "feedback": "Optimal linear scan."},
                    "communication": {"score": 92, "feedback": "High clarity."},
                    "coding_correctness": {"score": 92, "feedback": "Robust formulation."},
                    "strengths": ["Self-corrected negative array pitfall", "O(1) space optimization"],
                    "areas_for_improvement": ["Could briefly discuss Divide and Conquer alternative"],
                    "final_feedback": "Exceptional problem solving and algorithmic depth."
                }
            }
        ]

        for item in interview_templates:
            prob = Problem.objects.filter(slug=item["slug"]).first()
            if not prob:
                continue
            u = random.choice(users)
            session = InterviewSession.objects.create(
                user=u,
                problem=prob,
                difficulty=item["difficulty"],
                status='COMPLETED',
                current_stage='FINAL_EVALUATION'
            )
            interviews_count += 1

            for role, stage, msg in item["dialogue"]:
                InterviewMessage.objects.create(
                    interview_session=session,
                    role=role,
                    stage=stage,
                    message=msg
                )

            ev = item["evaluation"]
            InterviewEvaluation.objects.create(
                interview_session=session,
                overall_score=ev["overall_score"],
                problem_understanding=ev["problem_understanding"],
                approach_quality=ev["approach_quality"],
                technical_reasoning=ev["technical_reasoning"],
                complexity_analysis=ev["complexity_analysis"],
                edge_case_awareness=ev["edge_case_awareness"],
                optimization=ev["optimization"],
                communication=ev["communication"],
                coding_correctness=ev["coding_correctness"],
                strengths=ev["strengths"],
                areas_for_improvement=ev["areas_for_improvement"],
                final_feedback=ev["final_feedback"]
            )

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {interactions_count} coaching interactions and {interviews_count} interview sessions."
        ))
