import os
import json
import random
import argparse
from collections import defaultdict
from typing import Dict, Any, List

def session_problem_aware_split(
    input_file: str,
    output_dir: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
    held_out_problem_slugs: List[str] = None
):
    """
    Performs a Session-Aware and Problem-Aware split:
    1. Entire sessions (session_id) are assigned atomically to either train, validation, or test.
       Near-identical turns within a coaching session NEVER cross split boundaries.
    2. Selected held-out problems are routed exclusively to the test set to evaluate out-of-distribution
       generalization on unseen problems.
    3. The remaining sessions are randomly distributed according to the target ratios using a fixed seed.
    """
    random.seed(seed)
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file {input_file} does not exist.")

    os.makedirs(output_dir, exist_ok=True)

    # Default held-out problems for problem-level test isolation if not specified
    # Select problems across difficulties: easy (e.g. valid-parentheses), medium (e.g. coin-change)
    if held_out_problem_slugs is None:
        held_out_problem_slugs = ["valid-parentheses", "coin-change"]

    # Load all records and group by session_id
    records_by_session = defaultdict(list)
    total_records = 0

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            session_id = rec.get('session_id') or f"unknown_{rec.get('id')}"
            records_by_session[session_id].append(rec)
            total_records += 1

    train_records = []
    val_records = []
    test_records = []

    train_sessions = set()
    val_sessions = set()
    test_sessions = set()

    remaining_sessions = []

    # First pass: Allocate sessions on held-out test problems directly to test
    for session_id, records in records_by_session.items():
        prob_slug = records[0].get('problem_slug', '')
        if prob_slug in held_out_problem_slugs:
            test_records.extend(records)
            test_sessions.add(session_id)
        else:
            remaining_sessions.append((session_id, records))

    # Shuffle remaining sessions
    random.shuffle(remaining_sessions)

    # Target counts based on remaining records
    needed_for_test = max(0, int(total_records * test_ratio) - len(test_records))
    target_val = int(total_records * val_ratio)

    curr_val_count = 0
    curr_test_count = 0

    for session_id, records in remaining_sessions:
        r_count = len(records)
        if curr_test_count < needed_for_test:
            test_records.extend(records)
            test_sessions.add(session_id)
            curr_test_count += r_count
        elif curr_val_count < target_val:
            val_records.extend(records)
            val_sessions.add(session_id)
            curr_val_count += r_count
        else:
            train_records.extend(records)
            train_sessions.add(session_id)

    # Verification: Ensure ZERO session overlap between splits
    overlap_train_val = train_sessions.intersection(val_sessions)
    overlap_train_test = train_sessions.intersection(test_sessions)
    overlap_val_test = val_sessions.intersection(test_sessions)

    assert not overlap_train_val, f"Data leakage detected! Overlapping sessions between train and val: {overlap_train_val}"
    assert not overlap_train_test, f"Data leakage detected! Overlapping sessions between train and test: {overlap_train_test}"
    assert not overlap_val_test, f"Data leakage detected! Overlapping sessions between val and test: {overlap_val_test}"

    # Verify held-out problems do not leak into train
    train_problem_slugs = {r.get('problem_slug') for r in train_records}
    for hp in held_out_problem_slugs:
        assert hp not in train_problem_slugs, f"Problem leakage detected! Held-out problem '{hp}' found in training split!"

    # Write files
    train_path = os.path.join(output_dir, 'train.jsonl')
    val_path = os.path.join(output_dir, 'validation.jsonl')
    test_path = os.path.join(output_dir, 'test.jsonl')

    for path, data in [(train_path, train_records), (val_path, val_records), (test_path, test_records)]:
        with open(path, 'w', encoding='utf-8') as f:
            for rec in data:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')

    print(f"==================================================")
    print(f"SESSION-AWARE & PROBLEM-AWARE SPLIT COMPLETED")
    print(f"==================================================")
    print(f"Total examples:       {total_records}")
    print(f"Total unique sessions:{len(records_by_session)}")
    print(f"Held-out problems:    {held_out_problem_slugs}")
    print(f"Train split:          {len(train_records)} examples ({len(train_records)/total_records*100:.1f}%) | {len(train_sessions)} sessions -> {train_path}")
    print(f"Validation split:     {len(val_records)} examples ({len(val_records)/total_records*100:.1f}%) | {len(val_sessions)} sessions -> {val_path}")
    print(f"Test split:           {len(test_records)} examples ({len(test_records)/total_records*100:.1f}%) | {len(test_sessions)} sessions -> {test_path}")
    print(f"Split Session Overlap Check: PASSED (0 overlapping sessions)")
    print(f"Held-Out Problem Isolation:  PASSED (Held-out problems isolated to test set)")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Session-aware and problem-aware train/validation/test splitter.")
    parser.add_argument('--input', type=str, default='ml/data/processed/qlora_formatted.jsonl', help="Input QLoRA formatted JSONL")
    parser.add_argument('--output_dir', type=str, default='ml/data/processed', help="Output directory")
    parser.add_argument('--train_ratio', type=float, default=0.70, help="Train ratio (default: 0.70)")
    parser.add_argument('--val_ratio', type=float, default=0.15, help="Validation ratio (default: 0.15)")
    parser.add_argument('--test_ratio', type=float, default=0.15, help="Test ratio (default: 0.15)")
    parser.add_argument('--seed', type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    session_problem_aware_split(
        input_file=args.input,
        output_dir=args.output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed
    )
