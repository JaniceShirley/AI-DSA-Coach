import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
import torch

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from ml.evaluation.eval_base_model import BaseCoachEvaluator
from ml.inference.run_model import DSACoachInference

def run_model_comparison(
    eval_set_path: str = "ml/data/evaluation/eval_set.jsonl",
    base_model_name: str = "Qwen/Qwen2.5-Coder-0.5B-Instruct",
    adapter_path: str = "ml/models/adapters/dsa-coach-lora",
    output_path: str = "ml/evaluation/model_comparison_results.json",
    sample_limit: int = 15
) -> Dict[str, Any]:
    """
    Rigorously compares BASE MODEL vs FINE-TUNED QLoRA MODEL on the exact same held-out evaluation suite.
    Evaluates:
    - DSA Concept Coverage (%)
    - Hint Quality Score (0-100)
    - Hint Progression Score (0-100)
    - Relevance Score (0-100)
    - Solution Leakage Rate (%)
    - Code-Aware Coaching Score (0-100)
    - Complexity Reasoning Score (0-100)
    """
    print("==================================================")
    print("PHASE 6B — BASE MODEL VS FINE-TUNED MODEL EVALUATION")
    print("==================================================")

    if not os.path.exists(eval_set_path):
        raise FileNotFoundError(f"Evaluation set {eval_set_path} does not exist.")

    cases = []
    with open(eval_set_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    if sample_limit and sample_limit < len(cases):
        cases = cases[:sample_limit]

    print(f"Loaded {len(cases)} held-out evaluation scenarios.")

    # 1. Initialize Evaluator
    evaluator = BaseCoachEvaluator()

    # 2. Evaluate Base Model alone (no adapter)
    print("\n>>> Evaluating BASE MODEL (Zero-Shot, No LoRA Adapter)...")
    base_engine = DSACoachInference(
        base_model_name=base_model_name,
        adapter_path=None,
        use_adapter=False,
        load_in_4bit=True
    )

    base_eval_results = []
    for idx, case in enumerate(cases, start=1):
        prompt = base_engine.format_prompt(
            problem_title=case.get("problem_title", ""),
            difficulty=case.get("difficulty", "Easy"),
            topics=case.get("topics", []),
            description=case.get("problem_description", ""),
            student_code=case.get("student_code", ""),
            student_question=case.get("student_question", ""),
            hint_level=case.get("hint_level"),
            interaction_type=case.get("interaction_type", "hint")
        )
        resp = base_engine.generate(prompt, max_new_tokens=200, temperature=0.2)
        eval_res = evaluator.evaluate_response(case, resp)
        eval_res["model_type"] = "BASE_MODEL"
        base_eval_results.append(eval_res)
        print(f"  [Base Model] Evaluated case {idx}/{len(cases)} ({case.get('eval_id')})")

    # Clean up base engine memory before loading adapter
    del base_engine
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # 3. Evaluate Fine-Tuned Model (with LoRA adapter)
    print("\n>>> Evaluating FINE-TUNED MODEL (Base Model + QLoRA Adapter)...")
    finetuned_engine = DSACoachInference(
        base_model_name=base_model_name,
        adapter_path=adapter_path,
        use_adapter=True,
        load_in_4bit=True
    )

    ft_eval_results = []
    for idx, case in enumerate(cases, start=1):
        prompt = finetuned_engine.format_prompt(
            problem_title=case.get("problem_title", ""),
            difficulty=case.get("difficulty", "Easy"),
            topics=case.get("topics", []),
            description=case.get("problem_description", ""),
            student_code=case.get("student_code", ""),
            student_question=case.get("student_question", ""),
            hint_level=case.get("hint_level"),
            interaction_type=case.get("interaction_type", "hint")
        )
        resp = finetuned_engine.generate(prompt, max_new_tokens=200, temperature=0.2)
        eval_res = evaluator.evaluate_response(case, resp)
        eval_res["model_type"] = "FINE_TUNED_QLORA"
        ft_eval_results.append(eval_res)
        print(f"  [Fine-Tuned] Evaluated case {idx}/{len(cases)} ({case.get('eval_id')})")

    del finetuned_engine

    # 4. Compute Aggregate Comparative Metrics
    def calc_aggregates(results_list):
        n = len(results_list)
        return {
            "avg_hint_quality": round(sum(r["metrics"]["hint_quality_score"] for r in results_list) / n, 2),
            "avg_hint_progression": round(sum(r["metrics"]["hint_progression_score"] for r in results_list) / n, 2),
            "avg_concept_coverage_pct": round(sum(r["metrics"]["dsa_concept_coverage_pct"] for r in results_list) / n, 2),
            "avg_relevance": round(sum(r["metrics"]["relevance_score"] for r in results_list) / n, 2),
            "leakage_count": sum(1 for r in results_list if r["metrics"]["solution_leakage"]),
            "leakage_rate_pct": round(sum(1 for r in results_list if r["metrics"]["solution_leakage"]) / n * 100, 2),
            "avg_code_aware": round(sum(r["metrics"]["code_aware_coaching_score"] for r in results_list) / n, 2),
            "avg_complexity": round(sum(r["metrics"]["complexity_reasoning_score"] for r in results_list) / n, 2)
        }

    base_stats = calc_aggregates(base_eval_results)
    ft_stats = calc_aggregates(ft_eval_results)

    comparison_summary = {
        "evaluation_cases_count": len(cases),
        "base_model": {
            "name": base_model_name,
            "metrics": base_stats
        },
        "fine_tuned_qlora_model": {
            "base_model_name": base_model_name,
            "adapter_path": adapter_path,
            "metrics": ft_stats
        },
        "differences": {
            "delta_hint_quality": round(ft_stats["avg_hint_quality"] - base_stats["avg_hint_quality"], 2),
            "delta_concept_coverage_pct": round(ft_stats["avg_concept_coverage_pct"] - base_stats["avg_concept_coverage_pct"], 2),
            "delta_relevance": round(ft_stats["avg_relevance"] - base_stats["avg_relevance"], 2),
            "delta_leakage_rate_pct": round(ft_stats["leakage_rate_pct"] - base_stats["leakage_rate_pct"], 2),
            "delta_code_aware": round(ft_stats["avg_code_aware"] - base_stats["avg_code_aware"], 2),
            "delta_complexity": round(ft_stats["avg_complexity"] - base_stats["avg_complexity"], 2)
        },
        "detailed_comparisons": [
            {
                "eval_id": b["eval_id"],
                "problem": b["problem_slug"],
                "test_category": b["test_category"],
                "base_response": b["model_response"],
                "fine_tuned_response": ft["model_response"],
                "base_metrics": b["metrics"],
                "fine_tuned_metrics": ft["metrics"]
            }
            for b, ft in zip(base_eval_results, ft_eval_results)
        ]
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(comparison_summary, f, indent=2)

    # Print Summary Table
    print("\n==================================================")
    print("BASE MODEL VS FINE-TUNED MODEL COMPARISON RESULTS")
    print("==================================================")
    print(f"{'Evaluation Metric':<32} | {'Base Model':<12} | {'Fine-Tuned':<12} | {'Delta':<10}")
    print("-" * 75)
    print(f"{'1. Hint Quality (0-100)':<32} | {base_stats['avg_hint_quality']:<12} | {ft_stats['avg_hint_quality']:<12} | {comparison_summary['differences']['delta_hint_quality']:+<10}")
    print(f"{'2. Hint Progression (0-100)':<32} | {base_stats['avg_hint_progression']:<12} | {ft_stats['avg_hint_progression']:<12} | {round(ft_stats['avg_hint_progression'] - base_stats['avg_hint_progression'], 2):+<10}")
    print(f"{'3. DSA Concept Coverage (%)':<32} | {base_stats['avg_concept_coverage_pct']:<12}%| {ft_stats['avg_concept_coverage_pct']:<12}%| {comparison_summary['differences']['delta_concept_coverage_pct']:+<10}%")
    print(f"{'4. Relevance Score (0-100)':<32} | {base_stats['avg_relevance']:<12} | {ft_stats['avg_relevance']:<12} | {comparison_summary['differences']['delta_relevance']:+<10}")
    print(f"{'5. Solution Leakage Rate (%)':<32} | {base_stats['leakage_rate_pct']:<12}%| {ft_stats['leakage_rate_pct']:<12}%| {comparison_summary['differences']['delta_leakage_rate_pct']:+<10}%")
    print(f"{'6. Code-Aware Score (0-100)':<32} | {base_stats['avg_code_aware']:<12} | {ft_stats['avg_code_aware']:<12} | {comparison_summary['differences']['delta_code_aware']:+<10}")
    print(f"{'7. Complexity Reasoning (0-100)':<32} | {base_stats['avg_complexity']:<12} | {ft_stats['avg_complexity']:<12} | {comparison_summary['differences']['delta_complexity']:+<10}")
    print("==================================================")
    print(f"Detailed comparison saved to: {output_path}")

    return comparison_summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare Base Model vs Fine-Tuned Model.")
    parser.add_argument("--eval_set", type=str, default="ml/data/evaluation/eval_set.jsonl", help="Evaluation set path")
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-Coder-0.5B-Instruct", help="Base model identifier")
    parser.add_argument("--adapter", type=str, default="ml/models/adapters/dsa-coach-lora", help="Adapter path")
    parser.add_argument("--output", type=str, default="ml/evaluation/model_comparison_results.json", help="Output path")
    parser.add_argument("--sample_limit", type=int, default=15, help="Number of eval scenarios to run")
    args = parser.parse_args()

    run_model_comparison(
        eval_set_path=args.eval_set,
        base_model_name=args.base_model,
        adapter_path=args.adapter,
        output_path=args.output,
        sample_limit=args.sample_limit
    )
