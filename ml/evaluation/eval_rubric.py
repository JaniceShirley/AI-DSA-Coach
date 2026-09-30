"""
Evaluation Rubric and Automated Scoring Definitions for AI DSA Coach (Phase 6C).
Defines a 0-4 qualitative scale and deterministic automated scoring functions.
"""
from typing import Dict, Any, List

RUBRIC_LEVELS = {
    0: "Incorrect / Unacceptable: Completely wrong, irrelevant, or critically leaks complete runnable code on conceptual hints.",
    1: "Weak: Generic boilerplate, vague advice, or fails to address the student's question or code.",
    2: "Partially Correct: Identifies relevant data structures or algorithms but lacks clear progressive guidance.",
    3: "Good: Accurate Socratic guidance, appropriate for requested hint level, sound complexity analysis, no solution leakage.",
    4: "Strong: Exceptional pedagogical scaffolding, precise Big-O analysis, proactive edge-case awareness, perfectly calibrated."
}

def map_pct_to_rubric(score_pct: float) -> int:
    """Maps a 0-100 percentage score to a 0-4 rubric level."""
    if score_pct >= 85:
        return 4
    elif score_pct >= 70:
        return 3
    elif score_pct >= 50:
        return 2
    elif score_pct >= 30:
        return 1
    else:
        return 0
