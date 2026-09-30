# AI DSA Coach — End-to-End System Architecture

This document provides a comprehensive technical breakdown of the AI DSA Coach platform architecture, designed for technical interviews, engineering reviews, and production deployment audits.

---

## 1. High-Level System Architecture Diagram

```
                              ┌─────────────────────────┐
                              │      Student User       │
                              └────────────┬────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 PRESENTATION LAYER                                     │
│  React 18 + TypeScript + Vite + Tailwind CSS                                            │
│  ├── Monaco Editor (Syntax Highlighting, Real-time Editing)                            │
│  ├── AI Coach Panel (Progressive Hints, Challenges, Alternatives, Code Feedback)       │
│  ├── Mock Interview Room (Multi-Stage Dialogue, Code Association, Dynamic Rubrics)     │
│  └── Analytics & Dashboards (Recharts, Topic Mastery, Submission History)              │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ HTTPS / REST (JWT Bearer Auth)
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 APPLICATION API LAYER                                  │
│  Django 5 + Django REST Framework (DRF)                                                │
│  ├── Authentication Service (Custom User Model, SimpleJWT Tokens)                      │
│  ├── Problem & Test Suite Manager (30 Curated DSA Problems, Public/Private Cases)      │
│  ├── Progress & Analytics Aggregator (UserProblemProgress, Pass Rates, Streak Tracking)│
│  └── Interview Orchestrator (Stage Progression, Dialogue Turns, Rubric Evaluations)    │
└───────────────────┬──────────────────────────────────────────────┬─────────────────────┘
                    │                                              │
                    ▼                                              ▼
┌──────────────────────────────────────┐       ┌─────────────────────────────────────────┐
│          PERSISTENCE LAYER           │       │         EXECUTION SANDBOX LAYER         │
│  PostgreSQL (Primary Relational DB)  │       │  Docker-Isolated Execution Container    │
│  ├── users                           │       │  ├── Read-Only Root Filesystem          │
│  ├── problems & test_cases           │       │  ├── Non-Root Execution User            │
│  ├── submissions                     │       │  ├── Memory Cgroup Limit (256 MB)       │
│  ├── user_problem_progress           │       │  ├── CPU Quota (0.5 Cores)              │
│  ├── coaching_interactions           │       │  └── Network Disabled (`--network none`)│
│  └── interview_sessions & messages   │       └─────────────────────────────────────────┘
└──────────────────────────────────────┘
                    ▲
                    │
┌───────────────────┴────────────────────────────────────────────────────────────────────┐
│                             AI COACH & ML INFERENCE LAYER                              │
│                                                                                        │
│                                   AICoachService                                       │
│                                          │                                             │
│                           ┌──────────────┴──────────────┐                              │
│                           ▼                             ▼                              │
│                 Model Provider Factory          Fallback Handler                       │
│                 (`get_ai_provider()`)           (Mock / External API)                  │
│                           │                             ▲                              │
│          ┌────────────────┴────────────────┐            │ Failure / Timeout            │
│          ▼                                 ▼            │                              │
│  `AI_MODEL_BACKEND=base`        `AI_MODEL_BACKEND=finetuned` ──────────────┘           │
│  Base Model (Zero-Shot)         Fine-Tuned QLoRA Adapter                               │
│  Qwen2.5-Coder-0.5B-Instruct    `dsa-coach-lora-v1`                                    │
│  4-Bit NF4 BitsAndBytes         7 Target Linear Modules (q, k, v, o, gate, up, down)  │
│                                 Trained on 67 Validated SFT Coaching Interactions      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### A. Presentation Layer (Frontend)
- **Monaco Code Editor:** Interactive developer environment supporting Python syntax, indent guides, and automatic bracket closure.
- **AI Coach Panel:** Dedicated drawer providing progressive scaffolding:
  - *I'm Stuck:* Progressive hint requests (Levels 1–4).
  - *Challenge Me:* Probes student on Big-O space/time complexity and boundary conditions.
  - *Alternative Approach:* Contrasts different algorithmic paradigms (e.g. Hash Map vs Two Pointers).
  - *AI Feedback:* Reviews submission execution results, syntax errors, and runtime bottlenecks.
- **Mock Interview Room:** Stage-based technical interview simulation guiding candidate through `PROBLEM_INTRO` $\to$ `APPROACH` $\to$ `COMPLEXITY` $\to$ `EDGE_CASES` $\to$ `CODING` $\to$ `FINAL_EVALUATION`.

### B. Application & Persistence Layer (Backend)
- **Django REST Framework:** Stateless API endpoints secured via JWT authentication.
- **Relational Integrity:** PostgreSQL database models tracking:
  - `Problem` & `TestCase`: Constraints, public test cases for editor runs, private test cases for final submissions.
  - `Submission`: Code snapshots, execution runtime (ms), memory usage (MB), test results.
  - `CoachingInteraction`: Full audit trail of questions, student code snapshots, hint levels, and coach responses.
  - `InterviewSession` & `InterviewMessage`: Multi-turn dialogue history linked to final 8-dimension rubric evaluations.

### C. Docker-Isolated Code Execution Sandbox
- Executes arbitrary user-submitted Python code safely:
  - **Network Isolation:** `--network none` prevents external data exfiltration or socket connections.
  - **Resource Constraints:** Strict timeouts (3.0s wall time), memory limits (256 MB cgroup), and restricted process limits (`pids-limit=64`).
  - **Filesystem Security:** Mounted tmpfs for scratch execution, read-only root system, non-root user execution.

---

## 3. Machine Learning & QLoRA Fine-Tuning Pipeline

### Phase 6A: Dataset Preparation & Preprocessing
```
Django DB (Coaching + Interview Models)
                    │
                    ▼  `python manage.py export_ai_dataset`
Raw JSONL Export (`ml/data/raw/raw_interactions.jsonl`)
                    │
                    ▼  `ml/preprocessing/clean_dataset.py`
Quality Filter (Deduplication, Empty/Short removal, Leakage detection)
                    │
                    ├── Approved (100) -> `cleaned_interactions.jsonl`
                    └── Rejected (4)   -> `rejected_interactions.jsonl`
                    │
                    ▼  `ml/preprocessing/format_qlora.py`
Hugging Face Chat Template (`messages` format)
                    │
                    ▼  `ml/preprocessing/split_dataset.py`
Session-Aware & Problem-Aware Split (Seed 42)
                    ├── Train (67 examples, 22 sessions)
                    ├── Validation (16 examples, 6 sessions)
                    └── Held-Out Test (17 examples, 6 sessions, isolated problems)
```

### Phase 6B: QLoRA Fine-Tuning Architecture
- **Base Model:** `Qwen/Qwen2.5-Coder-0.5B-Instruct` (with target scaling configuration for `Qwen2.5-Coder-7B-Instruct` on Cloud GPU).
- **Quantization:** 4-bit NormalFloat (`nf4`) with double quantization via `bitsandbytes`.
- **LoRA Configuration:**
  - Rank ($r$): 16
  - Alpha ($\alpha$): 32
  - Dropout: 0.05
  - Target Modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`
  - Trainable Parameters: **8,798,208 (1.7497%)**
  - Frozen Parameters: **494,032,768 (98.2503%)**
- **Training Progression:** 3 epochs, 27 steps, effective batch size 8. Train loss: $2.8276 \to 1.2585$, Validation loss: $1.1957 \to 0.5048$.

### Phase 6C: Inference & Model Provider Abstraction
- **Abstraction:** [`DSACoachModel`](file:///Users/janiceshirley/AI-DSA-Coach/backend/apps/coaching/providers/dsa_coach_model.py) implements [`BaseAIProvider`](file:///Users/janiceshirley/AI-DSA-Coach/backend/apps/coaching/providers/base.py).
- **Configuration Switch:** Controlled via `AI_MODEL_BACKEND=finetuned|base|mock` without touching application endpoints.
- **Singleton Caching:** Loaded PyTorch model is cached in-memory across HTTP requests, avoiding repeated 11-second disk load times.
- **High-Availability Fallback:** If local weights or GPU resources fail, the system automatically falls back to `MockAIProvider` or external API without user disruption.

---

## 4. Empirical Evaluation & Leakage Comparison

Evaluated on 15 held-out scenarios across 8 DSA problems:

| Evaluation Dimension | Base Model (Zero-Shot) | Fine-Tuned Model (QLoRA) | Delta | Significance |
| :--- | :--- | :--- | :--- | :--- |
| **Hint Quality Score (0–100)** | 56.60 | **63.10** | **+6.50** | Socratic pedagogy improved |
| **Hint Progression (0–100)** | 90.67 | **100.00** | **+9.33** | Perfect level boundary adherence |
| **Solution Leakage Rate (%)** | 26.67% (4/15 leaked) | **6.67% (1/15 leaked)** | **-20.00%** | **4x drop in premature code leaks** |
| **DSA Concept Coverage (%)** | **20.99%** | 15.33% | -5.66% | Conversational brevity trade-off |
| **Relevance Score (0–100)** | **94.67** | 86.67 | -8.00 | Avoided quoting prompt verbatim |
| **Code-Aware Score (0–100)** | **87.33** | 74.00 | -13.33 | Avoided copying code into early hints |
| **Complexity Reasoning (0–100)** | **61.67** | 56.67 | -5.00 | Concise Big-O guidance |

---

## 5. Security & Isolation Safeguards
1. **Model Weights Isolation:** Model weights and LoRA adapters are never exposed to the frontend or served statically.
2. **API Key Security:** Zero LLM API keys are exposed to the client. All inference is processed server-side.
3. **Data Privacy:** User coaching histories and code submissions are scoped strictly by authenticated user IDs.
4. **Execution Containment:** Docker sandbox prevents arbitrary student code from accessing host network, environment variables, or databases.
