# Phase 6: AI DSA Coach Fine-Tuning, Dataset Pipeline & Baseline Architecture

## 1. Why Fine-Tuning is Being Used

While general-purpose instruction-tuned frontier models perform well on direct coding questions, they inherently fail at specialized pedagogy and coaching principles:
- **Premature Solution Generation:** Base instruction models default to outputting full, runnable solution code immediately when asked a question, preventing students from building independent problem-solving skills.
- **Lack of Multi-Tiered Progression:** Real coaching requires calibrated scaffolding:
  - *Level 1:* Conceptual intuition and invariant discovery.
  - *Level 2:* Directional guidance and optimal data structure selection.
  - *Level 3:* Strategic algorithm logic and state transitions.
  - *Level 4:* Detailed pseudocode and edge-case checkpoints without code leakage.
- **Socratic Challenge & Edge-Case Probing:** The coach must challenge candidate assumptions, verify worst-case time/space complexity (Big-O), and interrogate boundary conditions.
- **Domain Specialization:** Fine-tuning an open-source model allows private self-hosting, predictable low latency, zero external API vendor lock-in, and guaranteed compliance with strict coaching guidelines.

---

## 2. Dataset Structure

The export pipeline extracts interactions from Django's PostgreSQL/SQLite database models into structured JSONL records:

### Coaching Interaction Schema
```json
{
  "id": "coach_1",
  "source": "coaching_interaction",
  "session_id": "session_4_1_2149",
  "user_id": 4,
  "problem_id": 1,
  "problem_title": "Two Sum",
  "problem_slug": "two-sum",
  "problem_description": "Given an array of integers `nums` and an integer `target`...",
  "topic": ["Array", "Hash Table"],
  "difficulty": "easy",
  "student_code": "def twoSum(nums, target):\n    for i in range(len(nums)):...",
  "student_question": "My solution is too slow for large arrays. How can I improve it?",
  "hint_level": 1,
  "coach_response": "Notice how your nested loops take O(N^2) time by repeatedly scanning the rest of the array. For any given number `x`, what exact complementary value do you need to find, and how fast could you search for it?",
  "interaction_type": "hint",
  "submission_id": 1,
  "validation_status": "APPROVED",
  "quality_status": "PASSED_INITIAL_CHECKS",
  "rejection_reasons": [],
  "created_at": "2026-09-30T12:17:23.628824+00:00"
}
```

### Mock Technical Interview Interaction Schema
```json
{
  "id": "interview_19",
  "source": "interview_message",
  "session_id": "interview_session_3",
  "user_id": 2,
  "problem_id": 5,
  "problem_title": "Maximum Subarray",
  "problem_slug": "maximum-subarray",
  "problem_description": "Given an integer array `nums`, find the subarray with the largest sum...",
  "topic": ["Array", "Dynamic Programming"],
  "difficulty": "medium",
  "stage": "COMPLEXITY",
  "student_response": "We can solve this in O(N) time using Kadane's Algorithm. We maintain a current running sum and global max. If running sum drops below 0, we reset it.",
  "interviewer_response": "Why does resetting to 0 when negative work? What if all elements in the array are negative?",
  "interaction_type": "interview",
  "validation_status": "APPROVED",
  "quality_status": "PASSED_INITIAL_CHECKS",
  "rejection_reasons": [],
  "created_at": "2026-09-30T12:17:23.691168+00:00"
}
```

### Hugging Face / TRL Supervised Fine-Tuning (SFT) Format
All approved examples are converted into the modern `messages` format:
```json
{
  "id": "coach_1",
  "interaction_type": "hint",
  "hint_level": 1,
  "problem_slug": "two-sum",
  "difficulty": "easy",
  "session_id": "session_4_1_2149",
  "messages": [
    {
      "role": "system",
      "content": "You are an AI DSA Coach specializing in progressive, Socratic guidance. Your mission is to help students learn data structures and algorithms by providing targeted hints matched to the requested hint level. Strict rules: Never output full, copy-pasteable solutions or complete function definitions..."
    },
    {
      "role": "user",
      "content": "[PROBLEM CONTEXT]\nTitle: Two Sum\nDifficulty: Easy\nTopics: Array, Hash Table\nDescription:\nGiven an array...\n\n[STUDENT CODE]\n```python\ndef twoSum(nums, target):\n...\n```\n\n[STUDENT QUESTION]\nMy solution is too slow for large arrays. How can I improve it?\n\n[COACHING OBJECTIVE]\nTask: hint | Requested: Level 1 (Conceptual Intuition)"
    },
    {
      "role": "assistant",
      "content": "Notice how your nested loops take O(N^2) time by repeatedly scanning the rest of the array..."
    }
  ]
}
```

---

## 3. Data Cleaning Pipeline & Rules

AI-generated data is never assumed to be high-quality ground truth. The preprocessing pipeline (`ml/preprocessing/clean_dataset.py`) enforces strict validation rules:

1. **RULE 1 (Missing-Field Handling):** Rejects any record lacking problem metadata, student context (both code and question empty), or coach response.
2. **RULE 2 (Problem Metadata Validation):** Requires valid problem identifiers, non-empty descriptions, and standardized difficulty (`easy`, `medium`, `hard`).
3. **RULE 3 (Interaction Type Validation):** Allowed types strictly restricted to `hint`, `challenge`, `alternative`, `feedback`, `interview`.
4. **RULE 4 (Empty & Ultra-Short Response Removal):** Responses with `< 15` characters or pure trivial tokens (`"Ok."`, `"Yes."`) are rejected.
5. **RULE 5 (Solution Leakage Filtering):** Early hints (Levels 1–2) containing complete Python function definitions (`def ...` with `return`) or large un-sanitized code blocks are rejected.
6. **RULE 6 (Deduplication):** Identical `(problem_id, interaction_type, hint_level, student_input, student_code, coach_response)` tuples are detected and isolated.
7. **RULE 7 (Text Normalization):** Whitespace normalization, stripping carriage returns (`\r\n` -> `\n`), and trimming repeated empty lines.

Rejected examples are recorded with explicit reason codes in `ml/data/processed/rejected_interactions.jsonl`.

---

## 4. Leakage Prevention

Data leakage is a severe failure mode in ML:
- **Session Leakage:** Splitting multi-turn dialogue from the same coaching session across train and test causes artificial test score inflation.
- **Problem Leakage:** Training on all 30 problems leads the model to memorize specific test inputs rather than general algorithmic reasoning.

To prevent both modes of leakage:
1. **Atomic Session Allocation:** Splitting operates at the `session_id` level. All turns of a user session stay strictly together.
2. **Problem-Level Holdout:** Specific problems (e.g., `valid-parentheses`, `coin-change`) are withheld entirely from training and assigned exclusively to the evaluation/test sets.

---

## 5. Train / Validation / Test Split

Dataset split settings (`ml/configs/data_config.json`):
- **Train Split (67%):** 67 examples across 22 unique sessions.
- **Validation Split (16%):** 16 examples across 6 unique sessions.
- **Test Split (17%):** 17 examples across 6 unique sessions (including isolated held-out problems).
- **Random Seed:** 42 for deterministic reproducibility.
- **Overlap Verification:** Programmatic assertion confirms 0 overlapping sessions and 0 held-out problem leakage.

---

## 6. Model Selection

### Compute Environment Inspection
- **Hardware:** Apple Silicon M3 (8 CPU cores)
- **System Memory:** 8 GB Unified RAM
- **Available Disk Space:** 45 GB
- **Acceleration:** Apple MPS (Metal Performance Shaders), **No NVIDIA CUDA**, **No CUDA VRAM**
- **Assessment:** Local training of a 7B model using `bitsandbytes` 4-bit CUDA quantization is not supported on macOS and would cause severe memory thrashing on 8 GB unified RAM. Training must be executed in a dedicated cloud GPU environment.

### Primary Selected Model: `Qwen/Qwen2.5-Coder-7B-Instruct`
- **Parameters:** 7.61 Billion
- **License:** Apache 2.0 (permissive, open for research and commercial software)
- **Hugging Face / TRL Compatibility:** Native chat template, standard tokenizer, supported out-of-the-box by `trl.SFTTrainer`.
- **Reasoning / Coding Benchmark:** SOTA coding benchmark among sub-10B open models (rivals 30B+ models on HumanEval and MBPP).
- **Target Training Environment:** 1x NVIDIA A10G (24 GB) or NVIDIA L4 (24 GB) or A100 (40 GB).

### Lightweight Fallback: `Qwen/Qwen2.5-Coder-1.5B-Instruct`
- **Parameters:** 1.54 Billion
- **License:** Apache 2.0
- **Purpose:** Fast local prototyping and testing on Apple Silicon (fits comfortably in ~3 GB RAM using PyTorch MPS or Apple MLX).

---

## 7. Baseline Evaluation

Before performing any fine-tuning, a baseline is established using the held-out evaluation dataset (`ml/data/evaluation/eval_set.jsonl`) evaluated by `ml/evaluation/eval_base_model.py`.

### Baseline Evaluation Results (Current Base Model)
| Metric | Score | Target Post-Fine-Tuning |
| :--- | :--- | :--- |
| **Hint Quality Score** | **67.69 / 100** | > 88.0 / 100 |
| **Hint Progression Score** | **100.0 / 100** | 100.0 / 100 |
| **DSA Concept Coverage** | **11.0%** | > 85.0% |
| **Relevance Score** | **88.0 / 100** | > 95.0 / 100 |
| **Solution Leakage Rate** | **0.0% (0 / 15)** | 0.0% (Zero Leakage) |
| **Code-Aware Coaching Score** | **68.33 / 100** | > 90.0 / 100 |
| **Complexity Reasoning Score** | **76.67 / 100** | > 92.0 / 100 |

*Key Takeaway:* The base/mock coach demonstrates solid progression scaffolding (100%) and zero solution leakage (0%), but suffers from low DSA Concept Coverage (11%) on held-out algorithmic problems, clearly establishing the quantitative need for domain-specific fine-tuning.

---

## 8. Planned QLoRA Approach (Phase 6B)

Fine-tuning will be executed in Phase 6B using:
- **Quantization:** 4-bit NormalFloat (`nf4`) with double quantization and `bfloat16` compute dtype via `bitsandbytes`.
- **LoRA Hyperparameters:**
  - Rank ($r$): 16
  - Alpha ($\alpha$): 32
  - Dropout: 0.05
  - Target Modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`
- **Optimizer:** `paged_adamw_8bit`
- **Sequence Length:** 2048 tokens
- **Batch Size:** 2 per device, 8 gradient accumulation steps (effective batch size: 16)
- **Learning Rate:** $2 \times 10^{-4}$ with cosine decay schedule and 5% warmup.

---

## 9. Evaluation Metrics & Framework

1. **Hint Quality:** Pedagogical tone, clarity, absence of generic filler.
2. **Hint Progression:** Calibrated depth corresponding to Levels 1, 2, 3, or 4.
3. **DSA Correctness:** Verification of key algorithmic invariants and concepts against reference criteria.
4. **Relevance:** Context-awareness of student's question and specific problem constraints.
5. **Solution Leakage:** AST and heuristic verification that complete functions or answers are not spoiled.
6. **Code-Awareness:** Proactive reference to student variable names and syntax constructs.
7. **Complexity Reasoning:** Accurate Big-O analysis and space-time trade-off discussions.

---

## 10. Limitations

- **AST Heuristics:** Obfuscated code or solutions disguised as natural language prose cannot be 100% captured by syntactic parsers.
- **Dataset Size:** Initial dataset reflects 30 DSA problems. Scaling to 100+ problems will further improve generalization.
- **Evaluation Subjectivity:** While deterministic metrics (concept recall, AST leakage, regex complexity) provide reproducible benchmarks, qualitative human review remains necessary for assessing subtle pedagogical nuances.
