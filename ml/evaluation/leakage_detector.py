import re
import ast
from typing import Dict, Any, List, Tuple

class SolutionLeakageDetector:
    """
    Detector for identifying whether a coaching response inappropriately reveals complete solutions,
    copy-paste implementations, premature algorithmic spoilers, or excessive implementation details.

    Limitations:
    - Heuristics and AST parsing inspect syntactic and structural code patterns. Obfuscated code or
      code described in pure natural language prose without formal syntax may bypass AST analysis.
    - Contextual domain knowledge: Some small 1-line idiomatic expressions (e.g. `s.reverse()`) might
      be legitimate micro-hints or minor spoilers depending on problem context.
    """

    def __init__(self):
        # Algorithmic spoilers that should not be unilaterally named in Level 1 conceptual hints
        self.algorithm_spoilers = [
            r"kadane'?s\s+algorithm",
            r"boyer[\s-]moore",
            r"floyd'?s\s+cycle",
            r"dijkstra'?s",
            r"kmp\s+algorithm",
            r"rabin[\s-]karp",
            r"tarjan'?s",
            r"kosaraju'?s"
        ]

    def extract_code_blocks(self, text: str) -> List[str]:
        """Extract markdown fenced code blocks and inline code."""
        fenced = re.findall(r'```(?:python|py)?([\s\S]*?)```', text)
        return [b.strip() for b in fenced if b.strip()]

    def contains_complete_runnable_function(self, code: str) -> Tuple[bool, str]:
        """
        Uses Python AST parsing to verify if a code block is a complete, runnable function.
        """
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if function has a body with more than a pass/docstring
                    statements = [stmt for stmt in node.body if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))]
                    has_return = any(isinstance(s, ast.Return) for s in ast.walk(node))
                    if len(statements) >= 2 and has_return:
                        # Check if it has placeholder tokens
                        if "# TODO" not in code and "# Write your" not in code and "..." not in code:
                            return True, f"Found complete runnable function '{node.name}' with return statement."
        except SyntaxError:
            # Code snippet might be partial or contain pseudocode
            pass
        return False, ""

    def evaluate_leakage(self, response_text: str, hint_level: Any = 1, interaction_type: str = "hint") -> Dict[str, Any]:
        """
        Evaluates coaching response text for solution leakage.
        Returns detailed diagnostic dictionary.
        """
        if not response_text:
            return {
                "is_leaked": False,
                "leakage_severity": "NONE",
                "leakage_reasons": [],
                "code_ratio": 0.0,
                "contains_complete_function": False
            }

        reasons = []
        code_blocks = self.extract_code_blocks(response_text)
        total_code_chars = sum(len(b) for b in code_blocks)
        total_chars = max(len(response_text), 1)
        code_ratio = round(total_code_chars / total_chars, 3)

        contains_complete_func = False
        for block in code_blocks:
            is_func, func_msg = self.contains_complete_runnable_function(block)
            if is_func:
                contains_complete_func = True
                reasons.append(f"COMPLETE_FUNCTION_LEAK: {func_msg}")

        # Check for function headers and return statements outside fenced blocks
        has_def = bool(re.search(r'def\s+\w+\s*\([^)]*\)\s*(?:->[^:]+)?\s*:', response_text))
        has_return = 'return ' in response_text
        if has_def and has_return and not contains_complete_func:
            reasons.append("PROBABLE_FUNCTION_LEAK: Text contains function definition header and return statement.")

        # Hint-level specific rules
        try:
            level = int(hint_level) if hint_level is not None else 1
        except (ValueError, TypeError):
            level = 1

        if interaction_type == "hint":
            if level == 1:
                # Level 1 should be pure concept / questions. No code blocks or spoilers.
                if code_ratio > 0.15:
                    reasons.append(f"EXCESSIVE_CODE_RATIO: Level 1 hint has {code_ratio*100:.1f}% code content (max allowed: 15%).")
                for spoiler_pat in self.algorithm_spoilers:
                    if re.search(spoiler_pat, response_text, re.IGNORECASE):
                        reasons.append(f"PREMATURE_ALGORITHM_SPOILER: Specific named algorithm revealed prematurely in Level 1 hint.")
            elif level == 2:
                # Level 2 is directional (data structure selection). Code blocks should be minimal.
                if code_ratio > 0.30:
                    reasons.append(f"EXCESSIVE_CODE_RATIO: Level 2 hint has {code_ratio*100:.1f}% code content (max allowed: 30%).")
            elif level == 3:
                # Level 3 allows short snippets/logic, but not complete solutions
                if contains_complete_func:
                    reasons.append("COMPLETE_SOLUTION_IN_LEVEL_3: Level 3 should provide strategic logic, not copy-paste solution.")
            elif level == 4:
                # Level 4 allows detailed pseudocode/skeletons, but complete functional copy-paste solution is discouraged
                if contains_complete_func and "# [Full solution" not in response_text:
                    reasons.append("DIRECT_COPY_PASTE_SOLUTION: Level 4 should provide guided skeleton/pseudocode with checkpoints, not complete finished code.")

        is_leaked = len(reasons) > 0
        severity = "NONE"
        if is_leaked:
            if any("COMPLETE_FUNCTION" in r or "DIRECT_COPY_PASTE" in r for r in reasons):
                severity = "CRITICAL"
            elif any("PROBABLE_FUNCTION" in r or "COMPLETE_SOLUTION" in r for r in reasons):
                severity = "HIGH"
            else:
                severity = "MEDIUM"

        return {
            "is_leaked": is_leaked,
            "leakage_severity": severity,
            "leakage_reasons": reasons,
            "code_ratio": code_ratio,
            "contains_complete_function": contains_complete_func
        }

leakage_detector = SolutionLeakageDetector()
