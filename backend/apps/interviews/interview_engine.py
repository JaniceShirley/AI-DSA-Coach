"""
Senior Technical Interview Dialogue Engine.
Maintains state, tracks DSA conversation progression, acknowledges candidate points
without verbatim echoing, probes misconceptions, and asks one focused question at a time.
"""

import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class InterviewDialogueEngine:
    """
    Expert DSA technical interviewer simulation.
    Handles stage progression:
    PROBLEM_INTRO -> APPROACH -> COMPLEXITY -> OPTIMIZATION -> EDGE_CASES -> CODING -> FINAL_EVALUATION
    """

    @classmethod
    def conduct_turn(cls, context: Dict[str, Any]) -> Dict[str, Any]:
        problem = context.get('problem', {})
        problem_title = problem.get('title', 'Two Sum')
        problem_desc = problem.get('description', '')
        current_stage = context.get('stage', 'PROBLEM_INTRO')
        student_message = context.get('student_message', '').strip()
        dialogue_history = context.get('dialogue_history', [])
        latest_sub = context.get('latest_submission')

        is_two_sum = "two sum" in problem_title.lower()

        # STAGE 1: PROBLEM_INTRO
        if current_stage == 'PROBLEM_INTRO' or not student_message:
            intro_msg = (
                f"Hello! Welcome to your technical interview. Today we'll be tackling **{problem_title}**.\n\n"
                f"**Problem Statement:**\n{problem_desc}\n\n"
                f"To begin, how would you approach solving this problem? What initial thoughts or data structures come to mind?"
            )
            return {
                "stage": "APPROACH",
                "message": intro_msg,
                "should_advance_stage": True,
                "should_end": False
            }

        # Check what has happened in dialogue history
        history_text = " ".join([m.get('message', '').lower() for m in dialogue_history])
        msg_lower = student_message.lower()

        # STAGE 2: APPROACH
        if current_stage == 'APPROACH':
            is_explicit_sort = bool(re.search(r'\b(?:sort|sorted|sorting)\b', msg_lower)) and not bool(re.search(r'\bunsorted\b', msg_lower))

            # Case 1: Proposes two pointers on unsorted array or without sorting
            if ("two pointer" in msg_lower or "left and right" in msg_lower or "two pointers" in msg_lower) and not is_explicit_sort:
                return {
                    "stage": "APPROACH",
                    "message": (
                        "Two pointers are commonly useful when an array is sorted. "
                        "However, here the array is unsorted and we need to return the original indices. "
                        "How would you adapt that approach, or is there an alternative data structure you could use?"
                    ),
                    "should_advance_stage": False,
                    "should_end": False
                }

            # Case 2: Proposes Sorting + Two Pointers
            if is_explicit_sort and ("two pointer" in msg_lower or "pointer" in msg_lower or "binary search" in msg_lower):
                return {
                    "stage": "COMPLEXITY",
                    "message": (
                        "Sorting first and using two pointers is a valid technique. "
                        "What would be the time complexity of sorting, and how would you preserve the original indices required by the problem?"
                    ),
                    "should_advance_stage": True,
                    "should_end": False
                }

            # Case 3: Proposes Hash Map / Hash Table / Dictionary
            if any(term in msg_lower for term in ["hash map", "hashmap", "hash table", "hashtable", "dictionary", "hash set"]):
                return {
                    "stage": "COMPLEXITY",
                    "message": (
                        "Good. Using a hash map for constant-time lookups is a strong approach. "
                        "What would be the worst-case time complexity and space complexity of this solution?"
                    ),
                    "should_advance_stage": True,
                    "should_end": False
                }

            # Case 4: Proposes Brute Force / nested loops
            if any(term in msg_lower for term in ["brute force", "nested loop", "all pairs", "every pair", "check every", "iterate through all"]):
                return {
                    "stage": "COMPLEXITY",
                    "message": (
                        "Correct. In the brute-force approach, you check every pair of elements. "
                        "What would be the time and space complexity of this solution?"
                    ),
                    "should_advance_stage": True,
                    "should_end": False
                }

            # Case 5: Vague or minimal response
            if len(student_message.split()) < 4 or any(p in msg_lower for p in ["idk", "not sure", "don't know", "array"]):
                return {
                    "stage": "APPROACH",
                    "message": (
                        "Could you elaborate a bit more on how you would check if two numbers sum to the target? "
                        "What is the simplest way to test combinations of elements?"
                    ),
                    "should_advance_stage": False,
                    "should_end": False
                }

            # General default approach response
            return {
                "stage": "COMPLEXITY",
                "message": (
                    "That gives us a clear initial strategy. "
                    "What would be the worst-case time complexity and space complexity of this approach?"
                ),
                "should_advance_stage": True,
                "should_end": False
            }

        # STAGE 3: COMPLEXITY
        if current_stage == 'COMPLEXITY':
            has_o_n2 = bool(re.search(r'o\s*\(\s*n[²2\^]\s*\)|quadratic|n\s*squared', msg_lower))
            has_o_n = bool(re.search(r'o\s*\(\s*n\s*\)|linear', msg_lower))
            has_o_1 = bool(re.search(r'o\s*\(\s*1\s*\)|constant', msg_lower))
            has_o_nlogn = bool(re.search(r'o\s*\(\s*n\s*log\s*n\s*\)|nlogn', msg_lower))

            # If brute force was discussed in previous turns
            if "brute force" in history_text or "check every pair" in history_text:
                if has_o_n2:
                    return {
                        "stage": "OPTIMIZATION",
                        "message": (
                            "Spot on: O(n²) time due to the nested comparisons, and O(1) auxiliary space. "
                            "Given that O(n²) is slow for large inputs, can you think of a way to improve the time complexity?"
                        ),
                        "should_advance_stage": True,
                        "should_end": False
                    }
                elif has_o_n and not has_o_n2:
                    return {
                        "stage": "COMPLEXITY",
                        "message": (
                            "Notice that in the brute-force approach, for each element we must scan through the rest of the array in a nested loop. "
                            "Would that be linear, or does the number of comparisons grow quadratically?"
                        ),
                        "should_advance_stage": False,
                        "should_end": False
                    }

            # If hash map was discussed
            if "hash map" in history_text or "hash table" in history_text or "dictionary" in history_text:
                if has_o_n and (has_o_1 or "space" in msg_lower):
                    return {
                        "stage": "EDGE_CASES",
                        "message": (
                            "Exactly: O(n) time because hash map lookups are O(1) on average, and O(n) space to store the visited elements. "
                            "Before we write code, what edge cases or boundary conditions should we test against?"
                        ),
                        "should_advance_stage": True,
                        "should_end": False
                    }

            # If sorting was discussed
            if "sort" in history_text:
                if has_o_nlogn:
                    return {
                        "stage": "OPTIMIZATION",
                        "message": (
                            "Right, sorting takes O(n log n) time and the two-pointer pass is O(n). "
                            "Can we optimize the time complexity even further to O(n) using additional space?"
                        ),
                        "should_advance_stage": True,
                        "should_end": False
                    }

            # If complexity was answered reasonably
            if any(term in msg_lower for term in ["o(", "time", "space", "complexity"]):
                return {
                    "stage": "OPTIMIZATION",
                    "message": (
                        "Good analysis on the time and space complexity. "
                        "Can we optimize this solution further, or is there an alternative trade-off to consider?"
                    ),
                    "should_advance_stage": True,
                    "should_end": False
                }
            else:
                return {
                    "stage": "COMPLEXITY",
                    "message": (
                        "Could you state the Big-O time and space complexity explicitly? "
                        "For instance, how does the runtime scale with the size of the input array, n?"
                    ),
                    "should_advance_stage": False,
                    "should_end": False
                }

        # STAGE 4: OPTIMIZATION
        if current_stage == 'OPTIMIZATION':
            # Case 1: Proposes two pointers on unsorted or sorted array
            if "two pointer" in msg_lower or "pointer" in msg_lower:
                if "unsorted" in msg_lower or not is_explicit_sort:
                    return {
                        "stage": "OPTIMIZATION",
                        "message": (
                            "Two pointers are commonly useful when the array is sorted. "
                            "Since this array is unsorted, how would you adapt your approach?"
                        ),
                        "should_advance_stage": False,
                        "should_end": False
                    }
                elif is_explicit_sort:
                    return {
                        "stage": "OPTIMIZATION",
                        "message": (
                            "Sorting first would take O(n log n) time and would scramble the original indices. "
                            "Can we achieve an O(n) runtime without sorting by using extra space?"
                        ),
                        "should_advance_stage": False,
                        "should_end": False
                    }

            if any(term in msg_lower for term in ["hash map", "hashmap", "hash table", "dictionary", "hash set"]):
                if any(term in msg_lower for term in ["complement", "target -", "difference", "single pass", "index"]):
                    return {
                        "stage": "EDGE_CASES",
                        "message": (
                            "Good. By computing the complement (target - num) and checking if it exists in the hash map, we can solve this in a single O(n) pass. "
                            "What edge cases or potential pitfalls should we keep in mind before coding?"
                        ),
                        "should_advance_stage": True,
                        "should_end": False
                    }
                else:
                    return {
                        "stage": "OPTIMIZATION",
                        "message": (
                            "Good. Walk me through how the hash map helps you find the complement as you iterate."
                        ),
                        "should_advance_stage": False,
                        "should_end": False
                    }

            if "complement" in msg_lower or "target -" in msg_lower or "subtract" in msg_lower:
                return {
                    "stage": "EDGE_CASES",
                    "message": (
                        "Exactly, checking for the complement in O(1) time eliminates the need for the second loop. "
                        "What edge cases should we account for before implementing?"
                    ),
                    "should_advance_stage": True,
                    "should_end": False
                }

            return {
                "stage": "OPTIMIZATION",
                "message": (
                    "Can you think of a data structure that would allow O(1) lookups so we don't have to scan the array repeatedly?"
                ),
                "should_advance_stage": False,
                "should_end": False
            }

        # STAGE 5: EDGE_CASES
        if current_stage == 'EDGE_CASES':
            edge_terms = ["negative", "duplicate", "zero", "empty", "same element", "no solution", "large", "target", "two"]
            matched_edge = any(t in msg_lower for t in edge_terms)

            if matched_edge:
                return {
                    "stage": "CODING",
                    "message": (
                        "Good points, especially ensuring we don't use the same element twice and handling negative integers. "
                        "The problem constraints guarantee exactly one valid pair exists. "
                        "Let's move to implementation! Please open the code editor on the right and write your solution."
                    ),
                    "should_advance_stage": True,
                    "should_end": False
                }
            else:
                return {
                    "stage": "CODING",
                    "message": (
                        "Those are helpful considerations. We should also be careful not to use the same index twice, and account for negative values. "
                        "Let's move to implementation! Please write your solution in the code editor on the right and run the tests."
                    ),
                    "should_advance_stage": True,
                    "should_end": False
                }

        # STAGE 6: CODING
        if current_stage == 'CODING':
            if latest_sub:
                status = latest_sub.get('status')
                if status == 'ACCEPTED':
                    return {
                        "stage": "FINAL_EVALUATION",
                        "message": (
                            "Excellent work! Your code passed all test cases cleanly with optimal efficiency. "
                            "Are there any final thoughts you'd like to share, or are you ready for your final interview evaluation?"
                        ),
                        "should_advance_stage": True,
                        "should_end": False
                    }
                else:
                    return {
                        "stage": "CODING",
                        "message": (
                            f"Your solution produced: {status} ({latest_sub.get('test_cases_passed', 0)}/{latest_sub.get('total_test_cases', 0)} passed). "
                            "Take a look at the execution output—how might you refine your implementation?"
                        ),
                        "should_advance_stage": False,
                        "should_end": False
                    }

            if any(t in msg_lower for t in ["done", "finished", "ready", "submitted", "eval"]):
                return {
                    "stage": "FINAL_EVALUATION",
                    "message": (
                        "Great job navigating the problem from brute force to an optimal linear-time solution. "
                        "Let's proceed to the final performance evaluation."
                    ),
                    "should_advance_stage": True,
                    "should_end": True
                }

            return {
                "stage": "CODING",
                "message": (
                    "Feel free to write and test your solution in the editor on the right. "
                    "Let me know if you run into any questions or when you are ready to review."
                ),
                "should_advance_stage": False,
                "should_end": False
            }

        # STAGE 7: FINAL_EVALUATION
        return {
            "stage": "FINAL_EVALUATION",
            "message": (
                "Thank you for completing this technical interview. "
                "I've compiled your comprehensive evaluation report below covering problem solving, technical reasoning, complexity analysis, and communication."
            ),
            "should_advance_stage": False,
            "should_end": True
        }
