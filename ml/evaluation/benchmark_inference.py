import os
import sys
import time
import json
import psutil
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

def benchmark_inference(iterations: int = 3):
    print("==================================================")
    print("AI DSA COACH — INFERENCE PERFORMANCE BENCHMARK")
    print("==================================================")
    
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024 * 1024)

    # 1. Measure Loading Time
    t0 = time.time()
    from ml.inference.run_model import DSACoachInference
    engine = DSACoachInference(
        base_model_name="Qwen/Qwen2.5-Coder-0.5B-Instruct",
        adapter_path="ml/models/adapters/dsa-coach-lora",
        use_adapter=True,
        load_in_4bit=True
    )
    load_time = round(time.time() - t0, 3)
    mem_after_load = process.memory_info().rss / (1024 * 1024)
    model_memory_mb = round(mem_after_load - mem_before, 2)
    print(f"Model Load Time:    {load_time} s")
    print(f"Memory Footprint:   {model_memory_mb} MB")

    prompt = engine.format_prompt(
        problem_title="Two Sum",
        difficulty="Easy",
        topics=["Array", "Hash Table"],
        student_question="How can I improve my O(N^2) solution?",
        hint_level=1,
        interaction_type="hint"
    )

    # 2. First-response Latency (cold generation)
    t1 = time.time()
    first_resp = engine.generate(prompt, max_new_tokens=64)
    first_latency = round(time.time() - t1, 3)
    print(f"First-Response Latency: {first_latency} s")

    # 3. Subsequent Generation Latencies
    latencies = []
    token_counts = []
    for i in range(iterations):
        t_start = time.time()
        resp = engine.generate(prompt, max_new_tokens=64)
        elapsed = time.time() - t_start
        tokens = len(engine.tokenizer.encode(resp))
        latencies.append(elapsed)
        token_counts.append(tokens)
        print(f"  Run {i+1}: {elapsed:.3f} s ({tokens} tokens, {tokens/elapsed:.2f} tok/s)")

    avg_latency = round(sum(latencies) / len(latencies), 3)
    total_tokens = sum(token_counts)
    total_time = sum(latencies)
    throughput_tokens_sec = round(total_tokens / total_time, 2) if total_time > 0 else 0

    benchmark_data = {
        "hardware_environment": {
            "platform": sys.platform,
            "architecture": "Apple Silicon M3 (arm64, 8 CPU cores)",
            "unified_ram_gb": 8
        },
        "metrics": {
            "model_loading_time_seconds": load_time,
            "process_memory_mb": round(mem_after_load, 2),
            "model_memory_footprint_mb": model_memory_mb,
            "first_response_latency_seconds": first_latency,
            "average_generation_latency_seconds": avg_latency,
            "throughput_tokens_per_second": throughput_tokens_sec
        },
        "sample_output": first_resp
    }

    out_file = "ml/runs/inference_benchmark.json"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2)

    print("==================================================")
    print(f"Average Generation Latency: {avg_latency} s")
    print(f"Throughput:                 {throughput_tokens_sec} tokens/sec")
    print(f"Benchmark report saved to:  {out_file}")

if __name__ == "__main__":
    benchmark_inference(iterations=3)
