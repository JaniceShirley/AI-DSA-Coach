import os
import sys
import json
import re
import argparse
from pathlib import Path

# Add project root and backend to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'backend'))

from typing import Dict, Any, List
from ml.evaluation.leakage_detector import leakage_detector

class BaseCoachEvaluator:
    """
    Reproducible evaluation framework for assessing AI DSA Coach baseline model performance.
    Evaluates 7 core dimensions:
    1. Hint Quality
    2. Hint Progression
    3. DSA Correctness & Concept Coverage
    4. Relevance
    5. Solution Leakage
    6. Code-Aware Coaching
    7. Complexity Reasoning
    """

    def evaluate_response(self, eval_case: Dict[str, Any], model_response: Any) -> Dict[str, Any]:
        if isinstance(model_response, dict):
            if 'message' in model_response:
                resp_text = model_response['message']
            else:
                resp_text = "\n".join(f"**{k.replace('_', ' ').title()}:** {v}" for k, v in model_response.items() if isinstance(v, str))
        else:
            resp_text = str(model_response or "").strip()

        resp_text = resp_text.strip()
        resp_lower = resp_text.lower()
        hint_level = eval_case.get('hint_level')
        interaction_type = eval_case.get('interaction_type', 'hint')
        expected_concepts = [c.lower() for c in eval_case.get('expected_concepts', [])]
        prohibited_leakage = [p.lower() for p in eval_case.get('prohibited_leakage', [])]
        student_code = eval_case.get('student_code', '')
        student_q = eval_case.get('student_question', '')

        # 1. DSA Correctness & Concept Coverage (0 - 100)
        matched_concepts = []
        if expected_concepts:
            for concept in expected_concepts:
                # Check concept words
                words = concept.split()
                if all(w in resp_lower for w in words):
                    matched_concepts.append(concept)
            concept_coverage = round(len(matched_concepts) / len(expected_concepts) * 100, 1)
        else:
            concept_coverage = 100.0

        # 2. Solution Leakage Evaluation
        leak_result = leakage_detector.evaluate_leakage(
            response_text=resp_text,
            hint_level=hint_level,
            interaction_type=interaction_type
        )
        # Check specific prohibited leakage items
        for p in prohibited_leakage:
            if p in resp_lower:
                leak_result["is_leaked"] = True
                leak_result["leakage_reasons"].append(f"PROHIBITED_LEAKAGE_MATCH: '{p}' found in response.")
                leak_result["leakage_severity"] = "CRITICAL"

        # 3. Hint Progression Score (0 - 100)
        # Verifies that guidance depth appropriately matches requested hint level
        progression_score = 100
        progression_notes = []
        if hint_level == 1:
            if leak_result["code_ratio"] > 0.15:
                progression_score -= 40
                progression_notes.append("Level 1 should be conceptual; excessive code detected.")
            if "def " in resp_text:
                progression_score -= 50
                progression_notes.append("Level 1 should not contain function signatures.")
        elif hint_level == 2:
            if leak_result["code_ratio"] > 0.35:
                progression_score -= 30
                progression_notes.append("Level 2 should focus on directional guidance/data structures.")
        elif hint_level == 4:
            if len(resp_text) < 80:
                progression_score -= 30
                progression_notes.append("Level 4 should provide detailed step-by-step logic.")
        progression_score = max(0, progression_score)

        # 4. Relevance Score (0 - 100)
        # Checks if response references problem context, question, or key problem terminology
        relevance_score = 60
        prob_title_words = [w.lower() for w in eval_case.get('problem_title', '').split() if len(w) > 2]
        if any(w in resp_lower for w in prob_title_words):
            relevance_score += 20
        if any(w in resp_lower for w in student_q.lower().split() if len(w) > 4):
            relevance_score += 20
        relevance_score = min(100, relevance_score)

        # 5. Code-Aware Coaching Score (0 - 100)
        code_aware_score = 50
        if student_code:
            # Extract variable names and function names from student code
            var_candidates = set(re.findall(r'\b[a-zA-Z_]\w*\b', student_code))
            python_keywords = {'def', 'return', 'for', 'in', 'if', 'else', 'while', 'range', 'len', 'pass', 'list', 'int', 'str', 'bool'}
            user_vars = {v for v in var_candidates if v not in python_keywords and len(v) > 1}
            found_vars = [v for v in user_vars if v.lower() in resp_lower]
            if found_vars:
                code_aware_score += min(50, len(found_vars) * 15)
        else:
            code_aware_score = 80 # Conceptual questions without code
        code_aware_score = min(100, code_aware_score)

        # 6. Complexity Reasoning Score (0 - 100)
        complexity_score = 50
        has_big_o = bool(re.search(r'O\([1Nn]|O\(log|O\(n\^2', resp_text))
        mentions_time = 'time' in resp_lower or 'runtime' in resp_lower
        mentions_space = 'space' in resp_lower or 'memory' in resp_lower
        if has_big_o:
            complexity_score += 25
        if mentions_time or mentions_space:
            complexity_score += 25
        complexity_score = min(100, complexity_score)

        # 7. Overall Hint Quality Score (composite 0 - 100)
        # Penalizes leakage heavily
        quality_score = (
            0.25 * concept_coverage +
            0.20 * progression_score +
            0.15 * relevance_score +
            0.15 * code_aware_score +
            0.15 * complexity_score +
            (0 if leak_result["is_leaked"] else 10)
        )
        if leak_result["is_leaked"]:
            quality_score = max(0, quality_score - 40)
        quality_score = round(min(100.0, quality_score), 1)

        return {
            "eval_id": eval_case.get("eval_id"),
            "problem_slug": eval_case.get("problem_slug"),
            "interaction_type": interaction_type,
            "hint_level": hint_level,
            "test_category": eval_case.get("test_category"),
            "model_response": resp_text,
            "metrics": {
                "hint_quality_score": quality_score,
                "hint_progression_score": progression_score,
                "dsa_concept_coverage_pct": concept_coverage,
                "relevance_score": relevance_score,
                "solution_leakage": leak_result["is_leaked"],
                "leakage_severity": leak_result["leakage_severity"],
                "leakage_reasons": leak_result["leakage_reasons"],
                "code_aware_coaching_score": code_aware_score,
                "complexity_reasoning_score": complexity_score
            }
        }

    def evaluate_dataset(
        self,
        eval_set_path: str,
        output_results_path: str = 'ml/evaluation/baseline_results.json'
    ) -> Dict[str, Any]:
        """Evaluates baseline responses for all items in the evaluation dataset."""
        if not os.path.exists(eval_set_path):
            raise FileNotFoundError(f"Evaluation set {eval_set_path} does not exist.")

        cases = []
        with open(eval_set_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    cases.append(json.loads(line))

        # Import baseline provider for generating baseline responses
        from apps.coaching.providers.mock import MockAIProvider
        mock_provider = MockAIProvider()

        results = []
        for case in cases:
            # Generate baseline response using baseline coach logic
            ctx = {
                "problem": {
                    "id": 1,
                    "title": case.get("problem_title", ""),
                    "slug": case.get("problem_slug", ""),
                    "difficulty": case.get("difficulty", "easy"),
                },
                "student_code": case.get("student_code", ""),
                "hint_level": case.get("hint_level") or 1,
                "user_question": case.get("student_question", ""),
                "latest_submission": None
            }

            itype = case.get("interaction_type", "hint")
            if itype == "hint":
                resp = mock_provider.generate_hint(ctx)
            elif itype == "challenge":
                resp = mock_provider.challenge_understanding(ctx)
            elif itype == "alternative":
                resp = mock_provider.generate_alternative_approach(ctx)
            elif itype == "feedback":
                resp = mock_provider.generate_feedback(ctx)
            else:
                resp = (
                    f"Let's break down {case.get('problem_title')}. "
                    f"Notice that for this question: '{case.get('student_question')}', "
                    f"we need to analyze the data structures, time complexity O(N), and space trade-offs."
                )

            eval_res = self.evaluate_response(case, resp)
            results.append(eval_res)

        # Aggregate metrics
        n = len(results)
        avg_quality = round(sum(r["metrics"]["hint_quality_score"] for r in results) / n, 2)
        avg_progression = round(sum(r["metrics"]["hint_progression_score"] for r in results) / n, 2)
        avg_concept = round(sum(r["metrics"]["dsa_concept_coverage_pct"] for r in results) / n, 2)
        avg_relevance = round(sum(r["metrics"]["relevance_score"] for r in results) / n, 2)
        avg_code_aware = round(sum(r["metrics"]["code_aware_coaching_score"] for r in results) / n, 2)
        avg_complexity = round(sum(r["metrics"]["complexity_reasoning_score"] for r in results) / n, 2)
        leakage_count = sum(1 for r in results if r["metrics"]["solution_leakage"])
        leakage_rate = round(leakage_count / n * 100, 2)

        summary = {
            "total_eval_cases": n,
            "aggregate_metrics": {
                "average_hint_quality_score": avg_quality,
                "average_hint_progression_score": avg_progression,
                "average_dsa_concept_coverage_pct": avg_concept,
                "average_relevance_score": avg_relevance,
                "solution_leakage_rate_pct": leakage_rate,
                "leakage_incident_count": leakage_count,
                "average_code_aware_coaching_score": avg_code_aware,
                "average_complexity_reasoning_score": avg_complexity
            },
            "eval_cases": results
        }

        os.makedirs(os.path.dirname(os.path.abspath(output_results_path)), exist_ok=True)
        with open(output_results_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        print("==================================================")
        print("BASE MODEL BASELINE EVALUATION REPORT")
        print("==================================================")
        print(f"Total Held-Out Evaluation Cases: {n}")
        print(f"1. Hint Quality Score (0-100):         {avg_quality}")
        print(f"2. Hint Progression Score (0-100):     {avg_progression}")
        print(f"3. DSA Concept Coverage (%):           {avg_concept}%")
        print(f"4. Relevance Score (0-100):            {avg_relevance}")
        print(f"5. Solution Leakage Rate (%):          {leakage_rate}% ({leakage_count}/{n} leaked)")
        print(f"6. Code-Aware Coaching Score (0-100):  {avg_code_aware}")
        print(f"7. Complexity Reasoning Score (0-100): {avg_complexity}")
        print("==================================================")
        print(f"Detailed results saved to: {output_results_path}")

        return summary

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate baseline AI DSA Coach model.")
    parser.add_argument('--eval_set', type=str, default='ml/data/evaluation/eval_set.jsonl', help="Held-out eval set path")
    parser.add_argument('--output', type=str, default='ml/evaluation/baseline_results.json', help="Results output path")
    args = parser.parse_args()

    evaluator = BaseCoachEvaluator()
    evaluator.evaluate_dataset(args.eval_set, args.output)
