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
