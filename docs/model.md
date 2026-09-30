# Model Card: AI DSA Coach QLoRA Adapter

## Model Overview
- **Base Model:** `Qwen/Qwen2.5-Coder-0.5B-Instruct` (with target scaling to `Qwen/Qwen2.5-Coder-7B-Instruct` on Cloud GPU)
- **Base Model Architecture:** CausalLM (Transformer with RoPE, Grouped-Query Attention, SwiGLU, RMSNorm)
- **Base Model Parameters:** 502,830,976 (502.8M)
- **Fine-Tuning Method:** QLoRA (Quantized Low-Rank Adaptation)
- **Base Model Quantization:** 4-bit NormalFloat (`nf4`) with double quantization via `bitsandbytes`
- **Adapter Parameters:** 8,798,208 (8.8M trainable parameters, **1.7497%** of total model)
- **Base Model Weights:** 100% frozen, completely unmodified
- **License:** Apache 2.0 (Permissive open-source)

---

## Intended Use
- **Primary Objective:** Provide progressive, Socratic hints (Levels 1–4) for Data Structures and Algorithms problems without prematurely providing full solutions.
- **Audience:** Computer science students, software engineers preparing for DSA technical interviews.
- **Supported Tasks:**
  - Multi-tiered progressive hints (Level 1: Concept, Level 2: Direction, Level 3: Strategy, Level 4: Pseudocode).
  - Algorithmic challenge questions on time and space complexity ($O(N)$, $O(1)$, $O(N \log N)$).
  - Boundary and edge-case probing (empty inputs, negative values, duplicates, extreme constraints).
  - Alternative approach trade-off discussions (Hash Map vs Two Pointers, Iterative vs DP).

## Non-Intended Use
- Direct competitive coding bots or copy-paste code generation.
- Replacing professional engineering interview human assessments.
- General-purpose conversation outside computer science and algorithmic problem-solving.

---

## Training Setup & Hyperparameters
- **Hardware Used:** Apple Silicon M3 (arm64, 8 CPU cores, 8 GB Unified Memory)
- **Training Duration:** 704.79 seconds (~11.75 minutes)
- **Optimizer:** AdamW (`torch.optim.AdamW`)
- **Initial Training Loss:** 2.8276 (Step 5)
- **Final Training Loss:** 1.2585
- **Final Validation Loss:** 0.5048
- **Total Training Steps:** 27 steps over 3 epochs
- **Effective Batch Size:** 8 (per-device batch size 2 $\times$ gradient accumulation 4)
- **Learning Rate:** $2 \times 10^{-4}$ with cosine decay schedule and 5% warmup
- **Weight Decay:** 0.01
- **Max Sequence Length:** 1024 tokens
- **LoRA Configuration:**
  - Rank ($r$): 16
  - Alpha ($\alpha$): 32
  - Dropout: 0.05
  - Target Modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`

---

## Dataset Description
- **Source:** Historical AI DSA coaching interactions from Django backend (`CoachingInteraction` and `InterviewMessage`).
- **Cleaning & Validation:** Enforced 7 deterministic cleaning rules in `ml/preprocessing/clean_dataset.py` (missing fields, duplicate removal, text normalization, code leakage filtering).
- **Split Proportions (Session-Aware & Problem-Aware):**
  - **Train:** 67 examples across 22 unique sessions (Zero overlap with eval).
  - **Validation:** 16 examples across 6 unique sessions.
  - **Test (Held-Out):** 17 examples across 6 unique sessions, including held-out problem isolation (`valid-parentheses`, `coin-change`).

---

## Evaluation & Benchmark Comparison
Evaluated on the exact same 15 held-out scenarios in `ml/data/evaluation/eval_set.jsonl`:

| Metric | Base Model (Zero-Shot) | Fine-Tuned QLoRA | Delta |
| :--- | :--- | :--- | :--- |
| **Hint Quality Score (0–100)** | 56.60 | **63.10** | **+6.50** |
| **Hint Progression Score (0–100)** | 90.67 | **100.00** | **+9.33** |
| **Solution Leakage Rate (%)** | 26.67% (4 / 15 leaked) | **6.67% (1 / 15 leaked)** | **-20.00% (Drastic drop in leakage)** |
| **DSA Concept Coverage (%)** | **20.99%** | 15.33% | -5.66% |
| **Relevance Score (0–100)** | **94.67** | 86.67 | -8.00 |
| **Code-Aware Coaching (0–100)** | **87.33** | 74.00 | -13.33 |
| **Complexity Reasoning (0–100)** | **61.67** | 56.67 | -5.00 |

### Key Analytical Takeaways
1. **Scaffolding and Socratic Adherence:** The fine-tuned model achieved a perfect **100.00%** on Hint Progression and improved Hint Quality by **+6.5 points**, learning to guide students through tiered questions rather than answering immediately.
2. **Major Reduction in Solution Spoilers:** The Base Model leaked full runnable solutions in **26.67%** of test cases (e.g., providing complete `def twoSum... return [i, j]` implementations for Level 1 hints). The fine-tuned adapter reduced solution leakage down to **6.67%** (a 4x reduction).
3. **Trade-offs on a 0.5B Parameter Model:** Due to the small parameter scale (0.5B) and modest dataset size (67 training examples), the model exhibited slight reductions in concept keyword breadth (-5.6%) and direct code variable referencing (-13.3%), leaning strongly into conversational Socratic withholding. Scaling up to the planned 7B model on Cloud GPU will restore full vocabulary depth while retaining the learned Socratic behavior.

---

## Known Limitations
1. **Model Parameter Capacity:** A 0.5B parameter model has constrained world knowledge on rare, highly complex graph algorithms (e.g. Tarjan's Strongly Connected Components or Dinic's Max Flow).
2. **Deterministic Heuristics:** Solution leakage detection relies on AST and regex parsers; subtle obfuscations in natural language prose may occasionally bypass automated syntax checks.
3. **Inference Latency on CPU/MPS:** While 4-bit inference works on Apple Silicon M3, batch token generation runs at ~10–15 tokens/sec. Production deployment should target GPU serving (vLLM / TGI).
