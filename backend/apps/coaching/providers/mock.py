from typing import Dict, Any
from .base import BaseAIProvider

class MockAIProvider(BaseAIProvider):
    """
    Deterministic Mock AI Provider for local testing, fallback, and development without external API costs.
    Provides educational, problem-aware responses that strictly follow coaching principles (no full solution code).
    """

    def generate_hint(self, context: Dict[str, Any]) -> str:
        problem = context.get('problem', {})
        problem_title = problem.get('title', 'this problem')
        hint_level = context.get('hint_level', 1)
        student_code = context.get('student_code', '')
        latest_sub = context.get('latest_submission')

        sub_status = latest_sub.get('status') if latest_sub else None

        if hint_level == 1:
            return (
                f"**Level 1 — Conceptual Guidance**\n\n"
                f"For '{problem_title}', step back and think about what core property or state you need to track as you traverse the data structure. "
                f"What information do you need at each step to avoid redundant computation?"
            )
        elif hint_level == 2:
            return (
                f"**Level 2 — Directional Guidance**\n\n"
                f"Consider what data structure could provide fast lookups. "
                f"Would a hash table (dictionary/set) or a two-pointer technique allow you to check relevant values in O(1) or O(N) time?"
            )
        elif hint_level == 3:
            return (
                f"**Level 3 — Strategic Guidance**\n\n"
                f"Try storing each element (or index) in a hash map as you iterate through the input. "
                f"Before adding the current element, check if its required complement or matching condition is already in your map."
            )
        else: # Level 4
            status_note = f" (Latest submission result: {sub_status})" if sub_status else ""
            return (
                f"**Level 4 — Detailed Guidance**{status_note}\n\n"
                f"Walk through your loop step by step with a small example:\n"
                f"1. Initialize your state container before starting the loop.\n"
                f"2. For each element `x`, calculate what condition needs to be satisfied.\n"
                f"3. If it exists in your map, return the answer immediately.\n"
                f"4. Otherwise, save `x` to the map and continue.\n"
                f"Pay special attention to edge cases like duplicate values or empty inputs!"
            )

    def challenge_understanding(self, context: Dict[str, Any]) -> str:
        user_question = context.get('user_question', '').strip()
        problem = context.get('problem', {})
        problem_title = problem.get('title', 'this problem')

        if user_question:
            return (
                f"**Evaluating Your Explanation:**\n\n"
                f"Good effort! You noted: \"{user_question}\".\n\n"
                f"Follow-up challenge: What is the exact worst-case time complexity and space complexity of your approach? "
                f"How would your algorithm handle an empty input or an input with duplicate values?"
            )

        return (
            f"**Challenge Your Understanding ({problem_title}):**\n\n"
            f"1. **Complexity:** What is the Time and Space complexity of your current approach?\n"
            f"2. **Correctness:** Why does your approach hold true for all valid test cases?\n"
            f"3. **Edge Cases:** What happens when the input contains duplicates, negative numbers, or maximum constraints?\n"
            f"4. **Trade-offs:** Can you optimize space complexity if the array was already sorted?"
        )

    def generate_alternative_approach(self, context: Dict[str, Any]) -> str:
        problem = context.get('problem', {})
        problem_title = problem.get('title', 'this problem')

        return (
            f"**Alternative Approaches for {problem_title}:**\n\n"
            f"### Approach 1: Hash Map (Current Preferred)\n"
            f"- **Core Idea:** Store visited values in a hash map for O(1) average lookup.\n"
            f"- **Time Complexity:** O(N)\n"
            f"- **Space Complexity:** O(N)\n\n"
            f"### Approach 2: Sorting + Two Pointers\n"
            f"- **Core Idea:** Sort the array first, then use left and right pointers moving inward based on comparison.\n"
            f"- **Time Complexity:** O(N log N)\n"
            f"- **Space Complexity:** O(1) or O(N) depending on sorting algorithm.\n"
            f"- **Trade-off:** Uses less auxiliary memory, but sorting takes O(N log N) time and alters index positions."
        )

    def generate_feedback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        problem = context.get('problem', {})
        problem_title = problem.get('title', 'this problem')
        latest_sub = context.get('latest_submission')
        is_accepted = latest_sub.get('status') == 'ACCEPTED' if latest_sub else True

        return {
            "approach": f"Hash-based lookup / traversal approach for {problem_title}.",
            "correctness": "All test cases passed cleanly." if is_accepted else "Partial test cases passed. Review edge cases.",
            "time_complexity": "O(N) - Linear time traversal.",
            "space_complexity": "O(N) - Auxiliary space for tracking visited states.",
            "edge_cases": "Handled non-empty inputs. Ensure duplicate values and zero/negative boundary conditions are verified.",
            "optimization": "Consider whether in-place modifications or two-pointer techniques can optimize space if input is sorted."
        }

    def conduct_interview_turn(self, context: Dict[str, Any]) -> Dict[str, Any]:
        problem = context.get('problem', {})
        problem_title = problem.get('title', 'this problem')
        problem_desc = problem.get('description', '')
        current_stage = context.get('stage', 'PROBLEM_INTRO')
        student_message = context.get('student_message', '').strip()
        latest_sub = context.get('latest_submission')

        if current_stage == 'PROBLEM_INTRO':
            return {
                "stage": "APPROACH",
                "message": (
                    f"Hello! Welcome to your technical interview. Today we'll be tackling **{problem_title}**.\n\n"
                    f"**Problem Statement:**\n{problem_desc}\n\n"
                    f"To begin, how would you approach solving this problem? What initial thoughts or data structures come to mind?"
                ),
                "should_advance_stage": True,
                "should_end": False
            }

        elif current_stage == 'APPROACH':
            return {
                "stage": "COMPLEXITY",
                "message": (
                    f"I see your point regarding: \"{student_message}\". "
                    f"That's a sound starting direction. What would be the worst-case **Time Complexity** and **Space Complexity** of this approach?"
                ),
                "should_advance_stage": True,
                "should_end": False
            }

        elif current_stage == 'COMPLEXITY':
            return {
                "stage": "EDGE_CASES",
                "message": (
                    f"Good breakdown on the complexity. Now let's think about edge cases and boundary conditions. "
                    f"What scenarios (such as empty inputs, duplicates, negative numbers, or maximum constraints) should we test against?"
                ),
                "should_advance_stage": True,
                "should_end": False
            }

        elif current_stage == 'EDGE_CASES':
            return {
                "stage": "OPTIMIZATION",
                "message": (
                    f"Those are important edge cases to keep in mind. "
                    f"Before we jump into writing code, can we optimize our strategy further, or are there trade-offs with an alternative approach?"
                ),
                "should_advance_stage": True,
                "should_end": False
            }

        elif current_stage == 'OPTIMIZATION':
            return {
                "stage": "CODING",
                "message": (
                    f"Well reasoned. Let's move to the implementation! "
                    f"Please write your solution in the code editor, run the test cases, and let me know once you're confident with your submission."
                ),
                "should_advance_stage": True,
                "should_end": False
            }

        elif current_stage == 'CODING':
            sub_status = latest_sub.get('status') if latest_sub else 'ACCEPTED'
            return {
                "stage": "FINAL_EVALUATION",
                "message": (
                    f"Thank you for coding the solution (Submission status: {sub_status}). "
                    f"You've covered the approach, complexity, edge cases, and code implementation. Let's conclude the interview and review your performance report."
                ),
                "should_advance_stage": True,
                "should_end": True
            }

        else: # FINAL_EVALUATION or default
            return {
                "stage": "FINAL_EVALUATION",
                "message": "The interview has concluded. Thank you for your time and structured problem solving!",
                "should_advance_stage": False,
                "should_end": True
            }

    def evaluate_interview(self, context: Dict[str, Any]) -> Dict[str, Any]:
        problem = context.get('problem', {})
        problem_title = problem.get('title', 'DSA Problem')
        topics = problem.get('topics', ['Algorithms'])
        latest_sub = context.get('latest_submission')
        is_accepted = latest_sub.get('status') == 'ACCEPTED' if latest_sub else True

        score = 88 if is_accepted else 74

        return {
            "overall_score": score,
            "problem_understanding": {
                "rating": "Strong",
                "notes": f"Clearly understood requirements and constraints for {problem_title}."
            },
            "approach_quality": {
                "rating": "Strong",
                "notes": "Selected appropriate algorithmic technique and efficient data structures."
            },
            "technical_reasoning": {
                "rating": "Strong" if score > 80 else "Good",
                "notes": "Clearly explained algorithmic logic and decision trade-offs."
            },
            "complexity_analysis": {
                "rating": "Strong",
                "notes": "Accurately derived Time and Space complexity bounds."
            },
            "edge_case_awareness": {
                "rating": "Good",
                "notes": "Identified key edge cases including boundary sizes and duplicates."
            },
            "optimization": {
                "rating": "Good",
                "notes": "Analyzed trade-offs between time-optimal and space-optimal strategies."
            },
            "communication": {
                "rating": "Strong",
                "notes": "Clear, professional, and structured communication throughout the interview."
            },
            "coding_correctness": {
                "rating": "Strong" if is_accepted else "Needs Improvement",
                "notes": "Clean implementation passing automated test suites." if is_accepted else "Implementation required debugging on test cases."
            },
            "strengths": [
                f"Demonstrated solid algorithmic intuition for {problem_title}.",
                "Proactively analyzed time and space complexity trade-offs.",
                "Maintained structured and concise technical communication."
            ],
            "areas_for_improvement": [
                "Consider alternative in-place strategies for memory-constrained environments.",
                "Formulate comprehensive edge-case test suites before finalizing code."
            ],
            "final_feedback": (
                f"Overall strong performance in this mock technical interview on {problem_title}. "
                f"You articulated your approach clearly, reasoned about complexities, and demonstrated solid technical competency."
            ),
            "recommended_topics": topics if topics else ["Hash Table", "Two Pointers"],
            "recommended_problems": []
        }
