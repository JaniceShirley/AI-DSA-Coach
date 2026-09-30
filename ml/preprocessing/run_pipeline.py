import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from ml.preprocessing.clean_dataset import clean_dataset
from ml.preprocessing.format_qlora import format_dataset
from ml.preprocessing.split_dataset import session_problem_aware_split
from ml.preprocessing.dataset_stats import compute_statistics

def run_pipeline(
    raw_file: str = "ml/data/raw/raw_interactions.jsonl",
    cleaned_file: str = "ml/data/processed/cleaned_interactions.jsonl",
    rejected_file: str = "ml/data/processed/rejected_interactions.jsonl",
    qlora_file: str = "ml/data/processed/qlora_formatted.jsonl",
    processed_dir: str = "ml/data/processed",
    stats_file: str = "ml/data/processed/dataset_statistics.json",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42
):
    print(">>> STEP 1: Cleaning raw dataset and applying quality filters...")
    clean_dataset(raw_file, cleaned_file, rejected_file)

    print("\n>>> STEP 2: Formatting approved records into Hugging Face/TRL QLoRA format...")
    format_dataset(cleaned_file, qlora_file)

    print("\n>>> STEP 3: Executing session-aware & problem-aware train/val/test split...")
    session_problem_aware_split(
        input_file=qlora_file,
        output_dir=processed_dir,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        seed=seed
    )

    print("\n>>> STEP 4: Computing exact dataset statistics...")
    compute_statistics(
        raw_path=raw_file,
        cleaned_path=cleaned_file,
        rejected_path=rejected_file,
        train_path=os.path.join(processed_dir, "train.jsonl"),
        val_path=os.path.join(processed_dir, "validation.jsonl"),
        test_path=os.path.join(processed_dir, "test.jsonl"),
        output_json=stats_file
    )
    print("\n>>> PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run complete ML data preprocessing pipeline.")
    parser.add_argument('--raw', type=str, default='ml/data/raw/raw_interactions.jsonl', help="Raw JSONL input path")
    parser.add_argument('--seed', type=int, default=42, help="Random seed")
    args = parser.parse_args()

    run_pipeline(raw_file=args.raw, seed=args.seed)
