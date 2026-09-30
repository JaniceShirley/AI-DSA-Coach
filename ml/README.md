# AI DSA Coach — Machine Learning & Fine-Tuning Pipeline

This directory contains the dataset preparation, data quality validation, preprocessing, and baseline evaluation framework for the AI DSA Coach fine-tuning pipeline (Phase 6).

---

## Directory Overview

```
ml/
├── configs/                       # Configuration files (isolated from code)
│   ├── data_config.json          # Dataset paths, split ratios, filtering thresholds
│   ├── eval_config.json          # Evaluation dimensions, leakage thresholds
│   ├── model_config.json         # Base model, quantization, LoRA parameters
│   └── training_config.json      # Planned QLoRA training hyperparameters
├── data/
│   ├── evaluation/               # Fixed held-out evaluation test suite
│   │   └── eval_set.jsonl
│   ├── processed/                # Cleaned, split, and statistics data
│   │   ├── cleaned_interactions.jsonl
│   │   ├── dataset_statistics.json
│   │   ├── qlora_formatted.jsonl
│   │   ├── rejected_interactions.jsonl
│   │   ├── test.jsonl
│   │   ├── train.jsonl
│   │   └── validation.jsonl
│   └── raw/                      # Raw database export
│       └── raw_interactions.jsonl
├── evaluation/                   # Evaluation framework & leakage detector
│   ├── baseline_results.json     # Baseline evaluation results
│   ├── eval_base_model.py        # Reproducible 7-dimension evaluator
│   └── leakage_detector.py       # AST & heuristic solution leakage detector
├── preprocessing/                # Reproducible cleaning, formatting & splitting
│   ├── clean_dataset.py          # Data cleaning & rule-based validation
│   ├── dataset_stats.py          # Comprehensive dataset statistics generator
│   ├── format_qlora.py           # HF/TRL chat-template formatter
│   ├── run_pipeline.py           # End-to-end preprocessing runner
│   └── split_dataset.py          # Session-aware & problem-aware splitter
├── README.md                     # Operational documentation (this file)
└── requirements.txt              # ML fine-tuning dependencies (isolated from Django)
```

---

## Step-by-Step Execution Guide

### 1. Export Data from Django Database
Exports all coaching interactions (hints, challenges, alternatives, feedback) and mock interview messages into structured raw JSONL format:

```bash
# From workspace root:
USE_SQLITE=1 backend/venv/bin/python backend/manage.py export_ai_dataset
```

*Output:* `ml/data/raw/raw_interactions.jsonl`

*(Optional: To seed synthetic historical interactions for testing, run `USE_SQLITE=1 backend/venv/bin/python backend/manage.py seed_interactions --clear` first).*

---

### 2. Run Data Cleaning & Quality Validation
Applies missing-field checks, text normalization, duplicate removal, and early hint code-leakage detection:

```bash
python3 ml/preprocessing/clean_dataset.py \
  --input ml/data/raw/raw_interactions.jsonl \
  --output ml/data/processed/cleaned_interactions.jsonl \
  --rejected ml/data/processed/rejected_interactions.jsonl
```

---

### 3. Format Dataset for QLoRA / TRL SFTTrainer
Converts approved interactions into the modern Hugging Face chat-format (`messages` list with `system`, `user`, and `assistant` turns):

```bash
python3 ml/preprocessing/format_qlora.py \
  --input ml/data/processed/cleaned_interactions.jsonl \
  --output ml/data/processed/qlora_formatted.jsonl
```

---

### 4. Perform Session-Aware & Problem-Aware Split
Splits into `train.jsonl` (70%), `validation.jsonl` (15%), and `test.jsonl` (15%) ensuring zero session leakage and isolating held-out problems:

```bash
python3 ml/preprocessing/split_dataset.py \
  --input ml/data/processed/qlora_formatted.jsonl \
  --output_dir ml/data/processed \
  --train_ratio 0.70 \
  --val_ratio 0.15 \
  --test_ratio 0.15 \
  --seed 42
```

---

### 5. Generate Dataset Statistics Report
Calculates exact distributions by interaction type, difficulty, hint level, input/output text lengths, duplicates, and split counts:

```bash
python3 ml/preprocessing/dataset_stats.py \
  --output ml/data/processed/dataset_statistics.json
```

---

### 6. End-to-End Pipeline Shortcut
You can execute steps 2 through 5 in a single command:

```bash
python3 ml/preprocessing/run_pipeline.py
```

---

### 7. Run Baseline Evaluation
Evaluates the baseline coach against the 15 held-out test cases across all 7 evaluation dimensions:

```bash
backend/venv/bin/python ml/evaluation/eval_base_model.py \
  --eval_set ml/data/evaluation/eval_set.jsonl \
  --output ml/evaluation/baseline_results.json
```

---

## Hardware Environment & Training Setup

- **Local Machine:** Apple Silicon M3 with 8 GB Unified RAM.
- **Local Status:** Ready for pipeline execution, dataset preparation, and inference testing. Full 7B QLoRA backpropagation with 4-bit CUDA quantization cannot run on macOS without an NVIDIA GPU.
- **Recommended Cloud GPU for Phase 6B Training:** NVIDIA A10G (24 GB) or NVIDIA L4 (24 GB) on RunPod, Lambda Labs, or AWS EC2 `g5.xlarge`.
- **Target Model:** `Qwen/Qwen2.5-Coder-7B-Instruct` (Apache 2.0 license).
