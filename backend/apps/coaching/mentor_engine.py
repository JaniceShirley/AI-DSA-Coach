"""
Conversational DSA Reasoning Mentor Engine.

Implements the core learning cycle:
STUDENT'S APPROACH -> GUIDED IMPLEMENTATION -> CORRECTNESS VERIFICATION
-> COMPLEXITY ANALYSIS -> DISCOVERY OF OPTIMIZED APPROACHES -> COMPARISON

Strictly adheres to:
- Approach-aware coaching (respects student's chosen valid approach without early redirect).
- Minimal hint policy (one small clue at a time, no complete code dumps).
- Non-fabrication of execution results (verifies via CodeExecutionService).
- Misconception counterexamples and targeted questions.
- Time & auxiliary space complexity coaching.
- Approach comparison matrix.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from apps.problems.models import Problem, TestCase
from apps.submissions.services.execution_service import CodeExecutionService

logger = logging.getLogger(__name__)

class DSACoachDialogueEngine:
    """
    Stateful conversational dialogue and reasoning engine for DSA coaching.
    """

    @classmethod
    def process_turn(
        cls,
        problem: Problem,
        session_data: Dict[str, Any],
        student_message: str,
        student_code: str = "",
        run_code: bool = False
    ) -> Dict[str, Any]:
        """
        Processes a single conversational turn from the student.
        Returns updated state and the mentor's response.
        """
        msg = student_message.strip()
        msg_lower = msg.lower()

        # Session state unpack
        stage = session_data.get('stage', 'APPROACH_DISCOVERY')
        current_approach = session_data.get('current_approach') or {}
        explored_approaches = list(session_data.get('explored_approaches') or [])
        solution_status = session_data.get('solution_status', 'IN_PROGRESS')
        complexity_state = dict(session_data.get('complexity_state') or {})
        hints_provided = list(session_data.get('hints_provided') or [])
        misconceptions = list(session_data.get('misconceptions') or [])
        dialogue_history = list(session_data.get('dialogue_history') or [])

        execution_result = None
        if run_code and student_code.strip():
            test_cases = list(problem.test_cases.all())
            if test_cases:
                execution_result = CodeExecutionService.execute_code(
                    code=student_code,
                    test_cases=test_cases,
                    language="python"
                )

        # 1. Check for Stuck / Frustration / Confusion
        is_stuck = bool(re.search(
            r'\b(?:i am stuck|i\'m stuck|stuck|don\'t understand|do not understand|confused|lost|no idea|help me|can\'t figure)\b',
            msg_lower
        ))
        stuck_count = sum(1 for m in dialogue_history[-4:] if re.search(r'\b(?:stuck|don\'t understand|confused)\b', m.get('user', '').lower()))

        # 2. Check for Problem Understanding questions
        is_problem_clarification = bool(re.search(
            r'\b(?:explain the problem|what is the problem|don\'t understand the problem|what does .* mean|example|constraints)\b',
            msg_lower
        ))

        # 3. Check for Approach Proposals
        detected_approach = cls._detect_approach(msg_lower, problem)

        # 4. Check for Complexity queries or answers
        detected_complexity = cls._detect_complexity_statement(msg_lower)

        # 5. Check for Code Review / Debugging requests
        is_code_review = bool(re.search(
            r'\b(?:review my code|is my code (?:correct|good|right)|why is (?:my )?code failing|code feedback|debug my code|check my code)\b',
            msg_lower
        ))

        # --- DISPATCH LOGIC BASED ON CONVERSATION AND STAGE ---

        # Case A: Student is asking about the problem statement
        if is_problem_clarification and stage in ['UNDERSTANDING_PROBLEM', 'APPROACH_DISCOVERY']:
            stage = 'UNDERSTANDING_PROBLEM'
            response_text = (
                f"Let's break down the problem together! For **{problem.title}**:\n\n"
                f"{problem.description.splitlines()[0] if problem.description else 'You are given input to process.'}\n\n"
                f"Imagine you are given a concrete small input like `[1, 2, 3, 1]`. "
                f"What output would you expect, and why?"
            )
            return cls._build_response(
                response_text=response_text,
                stage=stage,
                current_approach=current_approach,
                explored_approaches=explored_approaches,
                solution_status=solution_status,
                complexity_state=complexity_state,
                hints_provided=hints_provided,
                misconceptions=misconceptions,
                execution_result=execution_result
            )

        # Case B: Student repeatedly stuck / confused
        if is_stuck:
            clue = cls._handle_stuck_student(problem, stage, current_approach, stuck_count)
            hints_provided.append(clue)
            return cls._build_response(
                response_text=clue,
                stage=stage,
                current_approach=current_approach,
                explored_approaches=explored_approaches,
                solution_status=solution_status,
                complexity_state=complexity_state,
                hints_provided=hints_provided,
                misconceptions=misconceptions,
                execution_result=execution_result
            )

        # Case C: Code execution / review / debugging request
        if (run_code and student_code.strip()) or is_code_review:
            return cls._handle_code_feedback(
                problem=problem,
                student_code=student_code,
                execution_result=execution_result,
                stage=stage,
                current_approach=current_approach,
                explored_approaches=explored_approaches,
                complexity_state=complexity_state,
                hints_provided=hints_provided,
                misconceptions=misconceptions
            )

        # Case D: Complexity analysis stage or complexity answer
        if (stage == 'COMPLEXITY_ANALYSIS' and (detected_complexity or 'complexity' in msg_lower)) or \
           (detected_complexity and 'complexity' in msg_lower and not detected_approach):
            return cls._handle_complexity_turn(
                msg_lower=msg_lower,
                detected_complexity=detected_complexity,
                stage=stage,
                current_approach=current_approach,
                explored_approaches=explored_approaches,
                complexity_state=complexity_state,
                hints_provided=hints_provided,
                misconceptions=misconceptions,
                execution_result=execution_result
            )

        # Case E: Approach proposal (or student is in APPROACH_DISCOVERY / OPTIMIZATION_DISCOVERY)
        if detected_approach:
            approach_type = detected_approach['type']
            is_valid = detected_approach['is_valid']

            # Check if approach is invalid with a known misconception
            if not is_valid:
                misconception_text = detected_approach.get('misconception', '')
                counterexample = detected_approach.get('counterexample', '')
                if misconception_text and misconception_text not in misconceptions:
                    misconceptions.append(misconception_text)

                response_text = (
                    f"That's an interesting thought! However, let's test that reasoning with a small counterexample:\n\n"
                    f"{counterexample}\n\n"
                    f"{detected_approach.get('guiding_question', 'What happens in that case?')}"
                )
                return cls._build_response(
                    response_text=response_text,
                    stage='APPROACH_DISCOVERY',
                    current_approach=current_approach,
                    explored_approaches=explored_approaches,
                    solution_status=solution_status,
                    complexity_state=complexity_state,
                    hints_provided=hints_provided,
                    misconceptions=misconceptions,
                    execution_result=execution_result
                )

            # Valid Approach Proposed!
            current_approach = detected_approach

            # Check if this is a new approach during optimization
            if stage in ['OPTIMIZATION_DISCOVERY', 'APPROACH_COMPARISON']:
                stage = 'OPTIMIZED_IMPLEMENTATION'
                response_text = (
                    f"Great insight! Recognizing that we can use {detected_approach['name']} is a powerful step forward. "
                    f"{detected_approach['first_step']}\n\n"
                    f"How would you begin writing this in the editor?"
                )
            else:
                # Student is starting with this approach (e.g., brute force, sorting, or set)
                # DO NOT REDIRECT TO OPTIMAL! Help them implement their chosen valid approach first!
                stage = 'GUIDED_IMPLEMENTATION'
                validation_note = ""
                if not detected_approach.get('is_optimal'):
                    validation_note = "Even though it might not be the most optimal yet, solving it with your idea first builds strong intuition! "

                response_text = (
                    f"That's a valid approach! {validation_note}"
                    f"Let's work through implementing **{detected_approach['name']}**.\n\n"
                    f"{detected_approach['first_step']}"
                )

            return cls._build_response(
                response_text=response_text,
                stage=stage,
                current_approach=current_approach,
                explored_approaches=explored_approaches,
                solution_status=solution_status,
                complexity_state=complexity_state,
                hints_provided=hints_provided,
                misconceptions=misconceptions,
                execution_result=execution_result
            )

        # Case F: Optimization discussion
        if stage == 'OPTIMIZATION_DISCOVERY' or 'optimize' in msg_lower or 'faster' in msg_lower:
            stage = 'OPTIMIZATION_DISCOVERY'
            response_text = cls._prompt_optimization(current_approach)
            return cls._build_response(
                response_text=response_text,
                stage=stage,
                current_approach=current_approach,
                explored_approaches=explored_approaches,
                solution_status=solution_status,
                complexity_state=complexity_state,
                hints_provided=hints_provided,
                misconceptions=misconceptions,
                execution_result=execution_result
            )

        # Case G: Approach comparison request
        if 'compare' in msg_lower or stage == 'APPROACH_COMPARISON':
            if len(explored_approaches) >= 2 or (current_approach and len(explored_approaches) >= 1):
                stage = 'APPROACH_COMPARISON'
                comparison_table = cls._format_approach_comparison(explored_approaches, current_approach)
                return cls._build_response(
                    response_text=comparison_table,
                    stage=stage,
                    current_approach=current_approach,
                    explored_approaches=explored_approaches,
                    solution_status=solution_status,
                    complexity_state=complexity_state,
                    hints_provided=hints_provided,
                    misconceptions=misconceptions,
                    execution_result=execution_result
                )

        # Default conversational step: provide a gentle guidance prompt
        response_text = cls._handle_general_message(msg, stage, current_approach)
        return cls._build_response(
            response_text=response_text,
            stage=stage,
            current_approach=current_approach,
            explored_approaches=explored_approaches,
            solution_status=solution_status,
            complexity_state=complexity_state,
            hints_provided=hints_provided,
            misconceptions=misconceptions,
            execution_result=execution_result
        )

    # ------------------------------------------------------------------
    # HELPER: Approach Detection
    # ------------------------------------------------------------------
    @classmethod
    def _detect_approach(cls, msg_lower: str, problem: Problem) -> Optional[Dict[str, Any]]:
        """
        Recognizes algorithmic approaches in natural language, distinguishing valid,
        non-optimal, and flawed reasoning without hardcoding a single favorite.
        """
        # Flawed reasoning 1: Checking only first and last elements
        if re.search(r'\b(?:first and last|ends of the array|endpoints|only ends)\b', msg_lower):
            return {
                "name": "First and Last Element Check",
                "type": "flawed_boundary_check",
                "is_valid": False,
                "is_optimal": False,
                "misconception": "Assuming duplicates or targets only appear at boundary indices",
                "counterexample": "Consider the array `[1, 2, 2, 4]`. The duplicate values `2` and `2` are in the middle.",
                "guiding_question": "If we only check the first element (`1`) and last element (`4`), will we detect the duplicate in the middle?"
            }

        # Flawed reasoning 2: Summing the array for duplicate detection
        if re.search(r'\b(?:sum of array|sum the array|add all elements)\b', msg_lower) and "contains duplicate" in problem.title.lower():
            return {
                "name": "Array Sum Heuristic",
                "type": "flawed_sum",
                "is_valid": False,
                "is_optimal": False,
                "misconception": "Assuming sum uniquely identifies duplicate elements without a known 1..N permutation",
                "counterexample": "Consider `[1, 4]` (sum = 5) and `[2, 3]` (sum = 5). Both have the same sum without duplicates.",
                "guiding_question": "Can different combinations of numbers produce the same sum without having duplicates?"
            }

        # Valid Approach 1: Brute Force (Nested comparisons / Compare each pair)
        if re.search(r'\b(?:brute force|nested loops?|compare (?:every|all|each) (?:pair|element)|two loops?|for each element.*compare)\b', msg_lower):
            return {
                "name": "Brute Force (Nested Loops)",
                "type": "brute_force",
                "is_valid": True,
                "is_optimal": False,
                "time_complexity": "O(N²)",
                "space_complexity": "O(1) auxiliary",
                "first_step": "Which elements should you compare? To avoid comparing an element with itself or repeating pairs, what should the inner loop iterate over?",
                "description": "Compares every pair of elements using nested iterations."
            }

        # Valid Approach 2: Sorting + Adjacent Scan
        if re.search(r'\b(?:sort|sorting|sort and check|adjacent|sort.*pointer)\b', msg_lower):
            return {
                "name": "Sorting + Adjacent Scan",
                "type": "sorting",
                "is_valid": True,
                "is_optimal": False,
                "time_complexity": "O(N log N)",
                "space_complexity": "O(1) to O(N) auxiliary (depending on sort algorithm)",
                "first_step": "Once the array is sorted, where will matching or relevant elements be located relative to each other?",
                "description": "Sorts the input array first, then scans adjacent neighbors."
            }

        # Valid Approach 3: Hash Set / Hash Map / Dictionary
        if re.search(r'\b(?:set|hash ?set|hash ?table|hash ?map|dict|dictionary|frequency map|seen)\b', msg_lower):
            return {
                "name": "Hash Set / Hash Map",
                "type": "hash_set",
                "is_valid": True,
                "is_optimal": True,
                "time_complexity": "O(N) expected",
                "space_complexity": "O(N) auxiliary",
                "first_step": "You need a way to remember elements you've already seen. Before adding each element into the set or dictionary, what check should you perform?",
                "description": "Uses a hash set or dictionary for O(1) average lookup of previously visited elements."
            }

        # Valid Approach 4: Two Pointers
        if re.search(r'\b(?:two pointers?|left and right pointer|two cursor)\b', msg_lower):
            return {
                "name": "Two Pointers",
                "type": "two_pointers",
                "is_valid": True,
                "is_optimal": True,
                "time_complexity": "O(N)",
                "space_complexity": "O(1) auxiliary",
                "first_step": "Where should the pointers start (e.g. opposite ends or together), and under what condition should each pointer move?",
                "description": "Maintains two pointers moving inward or forward based on comparison rules."
            }

        # Valid Approach 5: Binary Search
        if re.search(r'\b(?:binary search|log n|mid pointer|divide and conquer)\b', msg_lower):
            return {
                "name": "Binary Search",
                "type": "binary_search",
                "is_valid": True,
                "is_optimal": True,
                "time_complexity": "O(log N)",
                "space_complexity": "O(1) auxiliary",
                "first_step": "What invariant allows you to discard half the search space at each step?",
                "description": "Halves search interval at each step based on sorted order."
            }

        # Valid Approach 6: Generic / Alternative valid approaches (not in predefined catalog)
        if re.search(r'\b(?:bit manipulation|xor|bitmask|frequency array|bucket|stack|queue|recursion|heap|priority queue)\b', msg_lower):
            match = re.search(r'\b(bit manipulation|xor|bitmask|frequency array|bucket|stack|queue|recursion|heap|priority queue)\b', msg_lower)
            technique = match.group(1) if match else "heuristic"
            return {
                "name": f"Custom: {technique.title()}",
                "type": "custom_valid",
                "is_valid": True,
                "is_optimal": False,
                "time_complexity": "Depends on implementation",
                "space_complexity": "Depends on implementation",
                "first_step": f"Using {technique} is an intriguing strategy! How do you plan to use it to solve this specific problem?",
                "description": f"Custom strategy proposed by student utilizing {technique}."
            }

        return None

    # ------------------------------------------------------------------
    # HELPER: Complexity Statement Detection
    # ------------------------------------------------------------------
    @classmethod
    def _detect_complexity_statement(cls, msg_lower: str) -> Optional[Dict[str, Any]]:
        """
        Detects if the student is claiming a time or space complexity.
        """
        if "o(" in msg_lower or "o (" in msg_lower or "quadratic" in msg_lower or "linear" in msg_lower or "constant" in msg_lower:
            time_val = None
            if "o(n^2)" in msg_lower or "o(n2)" in msg_lower or "o(n*n)" in msg_lower or "quadratic" in msg_lower:
                time_val = "O(N²)"
            elif "o(n log n)" in msg_lower or "o(nlogn)" in msg_lower:
                time_val = "O(N log N)"
            elif "o(n)" in msg_lower or "linear" in msg_lower:
                time_val = "O(N)"
            elif "o(1)" in msg_lower or "constant" in msg_lower:
                time_val = "O(1)"

            space_val = None
            if "space" in msg_lower:
                if "o(1)" in msg_lower or "constant" in msg_lower:
                    space_val = "O(1)"
                elif "o(n)" in msg_lower or "linear" in msg_lower:
                    space_val = "O(N)"

            return {
                "raw": msg_lower,
                "time": time_val,
                "space": space_val
            }
        return None

    # ------------------------------------------------------------------
    # HELPER: Stuck Student Management
    # ------------------------------------------------------------------
    @classmethod
    def _handle_stuck_student(
        cls,
        problem: Problem,
        stage: str,
        current_approach: Dict[str, Any],
        stuck_count: int
    ) -> str:
        """
        Provides progressive minimal clues with relatable examples.
        Increases specificity gradually without giving away the full solution.
        """
        approach_type = current_approach.get('type', '')

        if stage == 'APPROACH_DISCOVERY' or not approach_type:
            if stuck_count == 0:
                return (
                    "No worries at all! Let's take it one small step at a time. "
                    "If you had to check for duplicates by hand on paper with `[1, 2, 3, 1]`, "
                    "what is the simplest comparison you would do first?"
                )
            else:
                return (
                    "Think of the simplest 'brute force' way: take the first number (`1`), "
                    "and compare it with each number that comes after it. "
                    "Does that sound like something we can write with a loop?"
                )

        if approach_type == 'brute_force':
            if stuck_count == 0:
                return (
                    "You have an outer loop picking element `i`. "
                    "What index should your inner loop start at so you only compare forward elements?"
                )
            else:
                return (
                    "Hint: If the outer loop is at index `i`, you want the inner loop `j` to check elements after `i`. "
                    "So `j` can start at `i + 1` up to the end of the list."
                )

        if approach_type == 'hash_set':
            if stuck_count == 0:
                return (
                    "You're tracking numbers you've already seen in a set `seen = set()`. "
                    "As you loop through each number `x`, what condition tells you that you found a duplicate?"
                )
            else:
                return (
                    "Hint: Before doing `seen.add(x)`, check `if x in seen:`. "
                    "If it's already there, what should the function return immediately?"
                )

        return (
            "Let's simplify: focus on what happens for one single element at a time. "
            "What condition needs to hold before we can conclude the answer?"
        )

    # ------------------------------------------------------------------
    # HELPER: Code Feedback & Verification
    # ------------------------------------------------------------------
    @classmethod
    def _handle_code_feedback(
        cls,
        problem: Problem,
        student_code: str,
        execution_result: Optional[Dict[str, Any]],
        stage: str,
        current_approach: Dict[str, Any],
        explored_approaches: List[Dict[str, Any]],
        complexity_state: Dict[str, Any],
        hints_provided: List[str],
        misconceptions: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluates student code, distinguishes errors, and never fabricates test results.
        """
        if not student_code.strip():
            return cls._build_response(
                response_text="I don't see any code in the editor yet. Try writing your initial structure or function definition!",
                stage=stage,
                current_approach=current_approach,
                explored_approaches=explored_approaches,
                solution_status='IN_PROGRESS',
                complexity_state=complexity_state,
                hints_provided=hints_provided,
                misconceptions=misconceptions,
                execution_result=execution_result
            )

        # Static checks if execution result is missing
        if not execution_result:
            test_cases = list(problem.test_cases.all())
            if test_cases:
                execution_result = CodeExecutionService.execute_code(student_code, test_cases, "python")

        if not execution_result:
            return cls._build_response(
                response_text="I looked at your code. Let's run it against the test cases using the **Run** button to see how it performs!",
                stage=stage,
                current_approach=current_approach,
                explored_approaches=explored_approaches,
                solution_status='IN_PROGRESS',
                complexity_state=complexity_state,
                hints_provided=hints_provided,
                misconceptions=misconceptions,
                execution_result=None
            )

        exec_status = execution_result.get('status')
        passed = execution_result.get('test_cases_passed', 0)
        total = execution_result.get('total_test_cases', 0)
        err_msg = execution_result.get('error_message') or ''

        # 1. Syntax Error
        if exec_status == 'SYNTAX_ERROR':
            clue = f"There's a syntax error preventing your code from executing: `{err_msg}`. Check your colons, parentheses, or indentation."
            return cls._build_response(
                response_text=clue,
                stage='DEBUGGING',
                current_approach=current_approach,
                explored_approaches=explored_approaches,
                solution_status='INCORRECT',
                complexity_state=complexity_state,
                hints_provided=hints_provided,
                misconceptions=misconceptions,
                execution_result=execution_result
            )

        # 2. Runtime Error
        if exec_status == 'RUNTIME_ERROR':
            clue = f"Your code ran into a runtime error: `{err_msg}`. Walk through your variables with a small example to see why this happened."
            return cls._build_response(
                response_text=clue,
                stage='DEBUGGING',
                current_approach=current_approach,
                explored_approaches=explored_approaches,
                solution_status='INCORRECT',
                complexity_state=complexity_state,
                hints_provided=hints_provided,
                misconceptions=misconceptions,
                execution_result=execution_result
            )

        # 3. Wrong Answer
        if exec_status == 'WRONG_ANSWER':
            results = execution_result.get('results', [])
            failing = next((r for r in results if not r.get('passed')), None)
            detail = ""
            if failing:
                detail = f" On input `{failing.get('input')}`, your code returned `{failing.get('actual_output')}`, but expected `{failing.get('expected_output')}`."

            # Bug isolation without dumping complete code
            bug_hint = "What happens if no duplicate is found after checking all elements? Make sure your function handles returning the default case."
            if "return True" in student_code and "return False" not in student_code:
                bug_hint = "Notice that if no matching condition is met, what does your function return?"
            elif "range(len(" in student_code and "range(i" not in student_code and current_approach.get('type') == 'brute_force':
                bug_hint = "Check your inner loop bounds: are you comparing an element with itself when `i == j`?"

            response_text = f"Your logic is on the right track ({passed}/{total} test cases passed), but has a small bug.{detail}\n\n{bug_hint}"
            return cls._build_response(
                response_text=response_text,
                stage='DEBUGGING',
                current_approach=current_approach,
                explored_approaches=explored_approaches,
                solution_status='INCORRECT',
                complexity_state=complexity_state,
                hints_provided=hints_provided,
                misconceptions=misconceptions,
                execution_result=execution_result
            )

        # 4. Accepted!
        if exec_status == 'ACCEPTED':
            app_record = {
                "name": current_approach.get('name', 'Implemented Solution'),
                "type": current_approach.get('type', 'custom'),
                "is_valid": True,
                "is_optimal": current_approach.get('is_optimal', False),
                "status": "VERIFIED",
                "time_complexity": current_approach.get('time_complexity', 'To be analyzed'),
                "space_complexity": current_approach.get('space_complexity', 'To be analyzed'),
                "tradeoffs": current_approach.get('description', '')
            }

            existing_idx = next((i for i, a in enumerate(explored_approaches) if a.get('name') == app_record['name']), None)
            if existing_idx is not None:
                explored_approaches[existing_idx] = app_record
            else:
                explored_approaches.append(app_record)

            stage = 'COMPLEXITY_ANALYSIS'
            approach_name = current_approach.get('name', 'Your approach')
            response_text = (
                f"🎉 Excellent work! Your **{approach_name}** passed all {total} test cases!\n\n"
                f"Now let's understand how much work it performs. "
                f"In the worst case, how does the execution time grow as the input size $N$ gets larger? What is the Time Complexity?"
            )
            return cls._build_response(
                response_text=response_text,
                stage=stage,
                current_approach=current_approach,
                explored_approaches=explored_approaches,
                solution_status='VERIFIED',
                complexity_state=complexity_state,
                hints_provided=hints_provided,
                misconceptions=misconceptions,
                execution_result=execution_result
            )

        # Default fallback
        return cls._build_response(
            response_text=f"Execution completed with status: {exec_status}. Let's examine the output and see what happens next.",
            stage=stage,
            current_approach=current_approach,
            explored_approaches=explored_approaches,
            solution_status=solution_status,
            complexity_state=complexity_state,
            hints_provided=hints_provided,
            misconceptions=misconceptions,
            execution_result=execution_result
        )

    # ------------------------------------------------------------------
    # HELPER: Complexity Analysis Turn
    # ------------------------------------------------------------------
    @classmethod
    def _handle_complexity_turn(
        cls,
        msg_lower: str,
        detected_complexity: Optional[Dict[str, Any]],
        stage: str,
        current_approach: Dict[str, Any],
        explored_approaches: List[Dict[str, Any]],
        complexity_state: Dict[str, Any],
        hints_provided: List[str],
        misconceptions: List[str],
        execution_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Guides the student through time and auxiliary space complexity analysis.
        Corrects mistakes with targeted reasoning clues.
        """
        app_type = current_approach.get('type', 'brute_force')

        # 1. Brute Force Analysis
        if app_type == 'brute_force':
            if detected_complexity and detected_complexity.get('time') == 'O(N²)':
                complexity_state['time'] = 'O(N²)'
                complexity_state['space'] = 'O(1) auxiliary'
                cls._update_explored_approach_complexity(explored_approaches, current_approach.get('name'), 'O(N²)', 'O(1)')

                stage = 'OPTIMIZATION_DISCOVERY'
                response_text = (
                    "Spot on! In the worst case, the outer loop runs $N$ times and the inner loop makes up to $N$ comparisons, giving **$O(N^2)$ time**.\n\n"
                    "Since we only use a couple of index pointers, the auxiliary space is **$O(1)$**.\n\n"
                    "Now, notice the limitation: this solution repeatedly compares elements. "
                    "Can you think of a way or data structure that could help us avoid comparing every pair?"
                )
                return cls._build_response(
                    response_text=response_text,
                    stage=stage,
                    current_approach=current_approach,
                    explored_approaches=explored_approaches,
                    solution_status='VERIFIED',
                    complexity_state=complexity_state,
                    hints_provided=hints_provided,
                    misconceptions=misconceptions,
                    execution_result=execution_result
                )

            if detected_complexity and detected_complexity.get('time') in ['O(N)', 'O(1)']:
                response_text = (
                    f"Let's trace that carefully. A single loop through $N$ elements takes $O(N)$ time. "
                    f"Here, for *each* element in the outer loop, the inner loop also traverses the remaining elements. "
                    f"If an array has 1,000 elements, roughly how many comparisons will take place?"
                )
                return cls._build_response(
                    response_text=response_text,
                    stage='COMPLEXITY_ANALYSIS',
                    current_approach=current_approach,
                    explored_approaches=explored_approaches,
                    solution_status='VERIFIED',
                    complexity_state=complexity_state,
                    hints_provided=hints_provided,
                    misconceptions=misconceptions,
                    execution_result=execution_result
                )

        # 2. Sorting Analysis
        if app_type == 'sorting':
            if detected_complexity and detected_complexity.get('time') == 'O(N log N)':
                complexity_state['time'] = 'O(N log N)'
                complexity_state['space'] = 'O(1) to O(N) auxiliary'
                cls._update_explored_approach_complexity(explored_approaches, current_approach.get('name'), 'O(N log N)', 'O(1) to O(N)')

                stage = 'OPTIMIZATION_DISCOVERY'
                response_text = (
                    "Exactly right! Standard comparison sorts like Timsort run in **$O(N \\log N)$ time**, "
                    "and the linear scan takes $O(N)$, so the overall time is dominated by $O(N \\log N)$.\n\n"
                    "Can we do even better? Could we achieve linear $O(N)$ time if we traded a bit of auxiliary memory?"
                )
                return cls._build_response(
                    response_text=response_text,
                    stage=stage,
                    current_approach=current_approach,
                    explored_approaches=explored_approaches,
                    solution_status='VERIFIED',
                    complexity_state=complexity_state,
                    hints_provided=hints_provided,
                    misconceptions=misconceptions,
                    execution_result=execution_result
                )

        # 3. Hash Set Analysis
        if app_type in ['hash_set', 'hash_map']:
            if detected_complexity and detected_complexity.get('time') == 'O(N)':
                complexity_state['time'] = 'O(N) expected'
                complexity_state['space'] = 'O(N) auxiliary'
                cls._update_explored_approach_complexity(explored_approaches, current_approach.get('name'), 'O(N) expected', 'O(N)')

                stage = 'APPROACH_COMPARISON' if len(explored_approaches) >= 2 else 'COMPLETED'
                comparison_msg = ""
                if len(explored_approaches) >= 2:
                    comparison_msg = "\n\n" + cls._format_approach_comparison(explored_approaches, current_approach)

                response_text = (
                    "Precisely! Hash set lookups and insertions take **$O(1)$ expected time** on average. "
                    "Since we iterate through the list once, the overall time is **$O(N)$**.\n\n"
                    "And in the worst case where all elements are distinct, the set stores up to $N$ items, "
                    f"giving **$O(N)$ auxiliary space**.{comparison_msg}"
                )
                return cls._build_response(
                    response_text=response_text,
                    stage=stage,
                    current_approach=current_approach,
                    explored_approaches=explored_approaches,
                    solution_status='VERIFIED',
                    complexity_state=complexity_state,
                    hints_provided=hints_provided,
                    misconceptions=misconceptions,
                    execution_result=execution_result
                )

        response_text = (
            f"Think about the operations in your solution: "
            f"How many times does each loop run, and what is the cost of operations inside it? "
            f"What is your estimate for Time Complexity (e.g. $O(N)$, $O(N^2)$, $O(N \\log N)$) and Auxiliary Space?"
        )
        return cls._build_response(
            response_text=response_text,
            stage='COMPLEXITY_ANALYSIS',
            current_approach=current_approach,
            explored_approaches=explored_approaches,
            solution_status='VERIFIED',
            complexity_state=complexity_state,
            hints_provided=hints_provided,
            misconceptions=misconceptions,
            execution_result=execution_result
        )

    # ------------------------------------------------------------------
    # HELPER: Optimization Prompt
    # ------------------------------------------------------------------
    @classmethod
    def _prompt_optimization(cls, current_approach: Dict[str, Any]) -> str:
        app_type = current_approach.get('type', '')
        if app_type == 'brute_force':
            return (
                "Your brute force solution works, but performing pairwise comparisons takes $O(N^2)$ time. "
                "What information could you remember so you don't need to re-scan previously seen elements?"
            )
        elif app_type == 'sorting':
            return (
                "Sorting brought the time down to $O(N \\log N)$. "
                "Can you think of a data structure that allows checking whether an item exists in $O(1)$ average time?"
            )
        return (
            "Is there another angle we could explore, perhaps trading time for space or vice versa?"
        )

    # ------------------------------------------------------------------
    # HELPER: Approach Comparison Table
    # ------------------------------------------------------------------
    @classmethod
    def _format_approach_comparison(
        cls,
        explored_approaches: List[Dict[str, Any]],
        current_approach: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Formats a clean markdown comparison of explored approaches.
        """
        lines = [
            "### ⚖️ Approach Comparison",
            "",
            "| Approach | Time Complexity | Auxiliary Space | Trade-off / Key Idea |",
            "| :--- | :--- | :--- | :--- |"
        ]

        seen_names = set()
        approaches = []
        for app in explored_approaches:
            if app.get('name') not in seen_names:
                approaches.append(app)
                seen_names.add(app.get('name'))

        if current_approach and current_approach.get('name') not in seen_names:
            approaches.append(current_approach)

        for app in approaches:
            name = app.get('name', 'Approach')
            time_comp = app.get('time_complexity', 'O(?)')
            space_comp = app.get('space_complexity', 'O(?)')
            tradeoff = app.get('tradeoffs') or app.get('description') or 'Standard trade-off'
            lines.append(f"| **{name}** | {time_comp} | {space_comp} | {tradeoff} |")

        lines.append("")
        lines.append(
            "> **Key Takeaway:** Notice the classic time-space trade-off! "
            "Brute force uses zero extra memory but takes quadratic time. "
            "A hash set gives linear time by utilizing $O(N)$ extra space."
        )
        return "\n".join(lines)

    @classmethod
    def _update_explored_approach_complexity(
        cls,
        explored_approaches: List[Dict[str, Any]],
        name: Optional[str],
        time_c: str,
        space_c: str
    ):
        if not name:
            return
        for app in explored_approaches:
            if app.get('name') == name:
                app['time_complexity'] = time_c
                app['space_complexity'] = space_c
                return

    # ------------------------------------------------------------------
    # HELPER: General Message Handling
    # ------------------------------------------------------------------
    @classmethod
    def _handle_general_message(cls, msg: str, stage: str, current_approach: Dict[str, Any]) -> str:
        if stage == 'GUIDED_IMPLEMENTATION':
            return (
                "You're in the implementation phase! Focus on translating your idea into code in the editor. "
                "What line or condition would you like to write next?"
            )
        elif stage == 'DEBUGGING':
            return (
                "Let's trace your code step-by-step. Try printing out variables or checking edge cases like single-element inputs."
            )
        elif stage == 'COMPLEXITY_ANALYSIS':
            return (
                "How many times do the loops run in your implementation? What do you think the worst-case Time Complexity is?"
            )
        return (
            "What idea or data structure comes to mind for solving this? "
            "Feel free to share any thought—even a simple brute force idea is a great place to begin!"
        )

    # ------------------------------------------------------------------
    # HELPER: Build Unified Response Dict
    # ------------------------------------------------------------------
    @classmethod
    def _build_response(
        cls,
        response_text: str,
        stage: str,
        current_approach: Dict[str, Any],
        explored_approaches: List[Dict[str, Any]],
        solution_status: str,
        complexity_state: Dict[str, Any],
        hints_provided: List[str],
        misconceptions: List[str],
        execution_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {
            "message": response_text,
            "stage": stage,
            "current_approach": current_approach,
            "explored_approaches": explored_approaches,
            "solution_status": solution_status,
            "complexity_state": complexity_state,
            "hints_provided": hints_provided,
            "misconceptions": misconceptions,
            "execution_result": execution_result
        }
