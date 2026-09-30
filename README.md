# AI DSA Coach

AI-powered Interactive Data Structures & Algorithms (DSA) Learning and Technical Interview Preparation Platform.

## 🚀 Overview
AI DSA Coach is designed around the core learning philosophy:
`Think → Attempt → Get Stuck → Get a Hint → Try Again → Solve → Explain → Master`

Rather than providing direct code solutions, the platform tracks problem attempts, evaluates code submissions, computes performance analytics, and prepares for fine-tuned LLM progressive coaching.

---

## 🏗️ Technology Stack

### Frontend
- **Framework:** React + TypeScript + Vite
- **Styling:** Tailwind CSS (Dark Mode / Developer Aesthetic)
- **Editor:** Monaco Editor (`@monaco-editor/react`)
- **Routing:** React Router v6
- **Data Visualization:** Recharts
- **HTTP Client:** Axios (with JWT interceptors)

### Backend
- **Framework:** Python 3.13 + Django 5 + Django REST Framework (DRF)
- **Authentication:** Django Auth + DRF SimpleJWT
- **Database:** PostgreSQL (with SQLite local fallback)
- **ORM & Migrations:** Django ORM & Django Migrations
- **Code Execution:** Isolated Docker Container Sandbox & Subprocess Sandbox with strict timeouts and resource limits.

---

## 📂 Architecture & Directory Structure

```text
ai-dsa-coach/
├── backend/
│   ├── manage.py
│   ├── config/              # Django settings, root URLs, WSGI, ASGI
│   ├── apps/
│   │   ├── users/           # Custom User model & SimpleJWT Auth APIs
│   │   ├── problems/        # 30 DSA Problems catalog & TestCase models
│   │   ├── progress/        # UserProblemProgress tracking & dashboard stats
│   │   ├── submissions/     # Code execution service, Run/Submit APIs, Analytics View
│   │   └── coaching/        # AIService stub abstraction for future LLM coaching
│   └── tests/               # Pytest suite (18 unit tests passing)
├── frontend/
│   ├── src/
│   │   ├── components/      # Navbar, CodeEditor (Monaco), ProtectedRoute, LoadingSpinner
│   │   ├── pages/           # Login, Register, Dashboard, Problems Explorer, Problem Detail, Analytics, Profile
│   │   ├── context/         # AuthContext (global state)
│   │   ├── services/        # api.ts, authService, problemService, progressService, submissionService, analyticsService
│   │   └── types/           # TypeScript interfaces
├── docs/
│   ├── code-execution.md    # Sandbox architecture & security parameters
│   └── database.md          # Database ER diagram & SQL/ORM aggregations
├── data/                    # Dataset storage for future ML fine-tuning
├── ml/                      # ML datasets, preprocessing, training & inference pipelines
├── docker/                  # Docker Compose & Dockerfile configurations
├── .env.example
├── .gitignore
└── README.md
```

---

## 🤖 Machine Learning & AI Coach Fine-Tuning (Phase 6)

The platform features a custom **QLoRA (Quantized Low-Rank Adaptation)** fine-tuned open-source model specialized in **Socratic DSA coaching**, progressive hint scaffolding, and solution leakage prevention.

### Architectural Flow
```
User
 │
 ▼
React Frontend (Monaco Editor & AI Coach Panel)
 │
 ▼ (REST API + JWT Bearer Auth)
Django REST API (Session Orchestration & Guardrails)
 │
 ▼
PostgreSQL Database (Problem Metadata, Interaction History, Rubrics)
 │
 ▼
AI Coach Service (`AICoachService`)
 │
 ▼
Model Provider Interface (`DSACoachModel`)
 ├── Mode: `finetuned` -> Qwen2.5-Coder-0.5B + `dsa-coach-lora-v1` (4-Bit NF4)
 ├── Mode: `base`      -> Qwen2.5-Coder-0.5B Zero-Shot (4-Bit NF4)
 └── Fallback          -> Deterministic Mock Coach / OpenAI-compatible API
```

### Why Fine-Tuning Was Used
General-purpose LLMs default to immediately outputting full runnable solutions, violating coaching principles. Fine-tuning teaches the model:
1. **Tiered Progressive Hints:** Level 1 (Intuition) $\to$ Level 2 (Data Structures) $\to$ Level 3 (Strategic Logic) $\to$ Level 4 (Pseudocode Checkpoints).
2. **Solution Leakage Suppression:** Strictly withholds complete runnable functions on early conceptual hints.
3. **Socratic Questioning:** Guides students toward identifying space-time complexity bounds and subtle edge cases independently.

### QLoRA Fine-Tuning Setup
- **Base Model:** `Qwen/Qwen2.5-Coder-0.5B-Instruct` (with scaling target `Qwen/Qwen2.5-Coder-7B-Instruct`)
- **Quantization:** 4-bit NormalFloat (`nf4`) with double quantization via `bitsandbytes`
- **LoRA Configuration:** $r=16, \alpha=32$, target modules: `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`
- **Trainable Parameters:** **8,798,208 (1.75%)** | Base frozen parameters: **494,032,768 (98.25%)**
- **Loss Convergence:** Train loss: $2.8276 \to 1.2585$ | Validation loss: $1.1957 \to 0.5048$ over 3 epochs

### Empirical Base vs Fine-Tuned Evaluation
Evaluated across 15 held-out test scenarios using deterministic AST code parsing and concept heuristics:

| Evaluation Dimension | Base Model (Zero-Shot) | Fine-Tuned QLoRA Model | Delta | Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Hint Quality Score (0–100)** | 56.60 | **63.10** | **+6.50** | Socratic guidance improved |
| **Hint Progression (0–100)** | 90.67 | **100.00** | **+9.33** | **Perfect level adherence** |
| **Solution Leakage Rate (%)** | 26.67% (4/15 leaked) | **6.67% (1/15 leaked)** | **-20.00%** | **4x drop in premature solution leaks** |
| **DSA Concept Coverage (%)** | **20.99%** | 15.33% | -5.66% | Conversational brevity trade-off |
| **Relevance Score (0–100)** | **94.67** | 86.67 | -8.00 | Avoided quoting prompt verbatim |
| **Code-Aware Score (0–100)** | **87.33** | 74.00 | -13.33 | Avoided copying student code into hints |
| **Complexity Reasoning (0–100)** | **61.67** | 56.67 | -5.00 | Concise Big-O guidance |

---

## ⚡ Quick Start & ML Operations

### 1. Run AI Coach with Fine-Tuned Model
To start the backend with the fine-tuned QLoRA model:
```bash
USE_SQLITE=1 AI_MODEL_BACKEND=finetuned backend/venv/bin/python backend/manage.py runserver 8000
```
*(Or set `AI_MODEL_BACKEND=base` for base model, or `AI_MODEL_BACKEND=mock` for deterministic fallback).*

### 2. Standalone Model Inference
```bash
# Run fine-tuned adapter inference
ml/venv/bin/python ml/inference/run_model.py \
  --problem "Two Sum" \
  --difficulty "Easy" \
  --hint_level 1 \
  --question "How can I optimize my O(N^2) solution?"

# Run base model inference (without adapter)
ml/venv/bin/python ml/inference/run_model.py \
  --problem "Two Sum" \
  --no_adapter \
  --question "How can I optimize my O(N^2) solution?"
```

### 3. Run Comparative Evaluation Pipeline
```bash
# Runs side-by-side evaluation on held-out test suite:
ml/venv/bin/python ml/evaluation/compare_models.py
```

### 4. Run Inference Performance Benchmark
```bash
# Measures model load time, memory footprint, and token throughput:
ml/venv/bin/python ml/evaluation/benchmark_inference.py
```

---

## 🧪 Testing & Verification

Run the full Django / Pytest test suite (all 40 tests passing):
```bash
USE_SQLITE=1 backend/venv/bin/pytest backend/tests/
```
*Output:* `40 passed in 7.47s`

Build the frontend bundle:
```bash
cd frontend && npm run build
```

---

## 🔒 Security & Isolation
* Student code is executed in an isolated Docker container with timeouts, memory limits, and network disabled.
* Model weights and LoRA adapters are kept strictly server-side.
* AI failure triggers graceful fallback to mock providers, preventing application crashes.

---

## 📑 Documentation Links
* [System Architecture & Data Flow](docs/architecture.md)
* [Final Model Evaluation Report](docs/final_evaluation.md)
* [Model Card (`dsa-coach-lora-v1`)](docs/model.md)
* [Fine-Tuning & Dataset Pipeline Documentation](docs/fine-tuning.md)
* [Training Run Report](docs/training_report.md)
* [Code Execution Sandbox Documentation](docs/code-execution.md)
* [Database Schema & SQL Analytics Documentation](docs/database.md)
