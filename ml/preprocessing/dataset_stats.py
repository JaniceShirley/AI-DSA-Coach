import os
import json
import argparse
from collections import Counter
from typing import Dict, Any, List

def compute_statistics(
    raw_path: str,
    cleaned_path: str,
    rejected_path: str,
    train_path: str = None,
    val_path: str = None,
    test_path: str = None,
    output_json: str = 'ml/data/processed/dataset_statistics.json'
) -> Dict[str, Any]:
    """Computes comprehensive, exact dataset statistics across all pipeline stages."""

    # 1. Read Raw
    raw_records = []
    if os.path.exists(raw_path):
        with open(raw_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    raw_records.append(json.loads(line))

    # 2. Read Rejected
    rejected_records = []
    rejection_reasons_counter = Counter()
    duplicate_count = 0
    if os.path.exists(rejected_path):
        with open(rejected_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    rejected_records.append(rec)
                    for r in rec.get('rejection_reasons', []):
                        cat = r.split(':')[0]
                        rejection_reasons_counter[cat] += 1
                        if cat == 'DUPLICATE_RECORD':
                            duplicate_count += 1

    # 3. Read Cleaned
    cleaned_records = []
    if os.path.exists(cleaned_path):
        with open(cleaned_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    cleaned_records.append(json.loads(line))

    # Stats on Cleaned
    interaction_types = Counter()
    difficulties = Counter()
    topics_counter = Counter()
    hint_levels = Counter()

    input_char_lengths = []
    input_word_lengths = []
    output_char_lengths = []
    output_word_lengths = []

    for r in cleaned_records:
        itype = r.get('interaction_type', 'unknown')
        interaction_types[itype] += 1

        diff = r.get('difficulty', 'unknown').lower()
        difficulties[diff] += 1

        topics = r.get('topic', [])
        if isinstance(topics, list):
            for t in topics:
                topics_counter[t] += 1
        elif isinstance(topics, str):
            topics_counter[topics] += 1

        hl = r.get('hint_level')
        if hl is not None:
            hint_levels[f"level_{hl}"] += 1
        else:
            hint_levels["not_applicable"] += 1

        # Text length calculations
        if itype == 'interview':
            inp_text = (r.get('student_response') or '')
            out_text = (r.get('interviewer_response') or '')
        else:
            inp_text = (r.get('student_question') or '') + ' ' + (r.get('student_code') or '')
            out_text = (r.get('coach_response') or '')

        input_char_lengths.append(len(inp_text))
        input_word_lengths.append(len(inp_text.split()))
        output_char_lengths.append(len(out_text))
        output_word_lengths.append(len(out_text.split()))

    # Read Splits if available
    def count_file(path):
        if path and os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return sum(1 for line in f if line.strip())
        return 0

    train_count = count_file(train_path)
    val_count = count_file(val_path)
    test_count = count_file(test_path)

    avg_input_chars = sum(input_char_lengths) / len(input_char_lengths) if input_char_lengths else 0.0
    avg_input_words = sum(input_word_lengths) / len(input_word_lengths) if input_word_lengths else 0.0
    avg_output_chars = sum(output_char_lengths) / len(output_char_lengths) if output_char_lengths else 0.0
    avg_output_words = sum(output_word_lengths) / len(output_word_lengths) if output_word_lengths else 0.0

    stats = {
        "overview": {
            "total_raw_interactions": len(raw_records),
            "total_valid_interactions": len(cleaned_records),
            "total_rejected_interactions": len(rejected_records),
            "duplicate_count": duplicate_count,
            "validation_pass_rate_pct": round(len(cleaned_records) / max(len(raw_records), 1) * 100, 2)
        },
        "interaction_type_counts": {
            "hint": interaction_types.get("hint", 0),
            "challenge": interaction_types.get("challenge", 0),
            "alternative": interaction_types.get("alternative", 0),
            "feedback": interaction_types.get("feedback", 0),
            "interview": interaction_types.get("interview", 0)
        },
        "rejection_breakdown": dict(rejection_reasons_counter),
        "difficulty_distribution": dict(difficulties),
        "topic_distribution": dict(sorted(topics_counter.items(), key=lambda x: -x[1])),
        "hint_level_distribution": dict(sorted(hint_levels.items())),
        "text_length_statistics": {
            "average_input_char_length": round(avg_input_chars, 2),
            "average_input_word_count": round(avg_input_words, 2),
            "average_output_char_length": round(avg_output_chars, 2),
            "average_output_word_count": round(avg_output_words, 2),
            "min_output_char_length": min(output_char_lengths) if output_char_lengths else 0,
            "max_output_char_length": max(output_char_lengths) if output_char_lengths else 0
        },
        "splits": {
            "train": train_count,
            "validation": val_count,
            "test": test_count,
            "total_split_examples": train_count + val_count + test_count
        }
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

    # Print summary
    print("==================================================")
    print("DATASET STATISTICS REPORT")
    print("==================================================")
    print(f"Total raw interactions:      {stats['overview']['total_raw_interactions']}")
    print(f"Total valid interactions:    {stats['overview']['total_valid_interactions']}")
    print(f"Total rejected interactions: {stats['overview']['total_rejected_interactions']}")
    print(f"Duplicates identified:       {stats['overview']['duplicate_count']}")
    print(f"Pass rate:                   {stats['overview']['validation_pass_rate_pct']}%")
    print("\n--- Interaction Types ---")
    for k, v in stats['interaction_type_counts'].items():
        print(f"  {k:12}: {v}")
    print("\n--- Difficulty Distribution ---")
    for k, v in stats['difficulty_distribution'].items():
        print(f"  {k:12}: {v}")
    print("\n--- Hint Level Distribution ---")
    for k, v in stats['hint_level_distribution'].items():
        print(f"  {k:16}: {v}")
    print("\n--- Text Length Averages ---")
    print(f"  Average input:  {stats['text_length_statistics']['average_input_char_length']} chars ({stats['text_length_statistics']['average_input_word_count']} words)")
    print(f"  Average output: {stats['text_length_statistics']['average_output_char_length']} chars ({stats['text_length_statistics']['average_output_word_count']} words)")
    print("\n--- Dataset Splits ---")
    print(f"  Train:      {stats['splits']['train']}")
    print(f"  Validation: {stats['splits']['validation']}")
    print(f"  Test:       {stats['splits']['test']}")
    print(f"\nStatistics saved to: {output_json}")

    return stats

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate dataset statistics report.")
    parser.add_argument('--raw', type=str, default='ml/data/raw/raw_interactions.jsonl', help="Raw JSONL path")
    parser.add_argument('--cleaned', type=str, default='ml/data/processed/cleaned_interactions.jsonl', help="Cleaned JSONL path")
    parser.add_argument('--rejected', type=str, default='ml/data/processed/rejected_interactions.jsonl', help="Rejected JSONL path")
    parser.add_argument('--train', type=str, default='ml/data/processed/train.jsonl', help="Train JSONL path")
    parser.add_argument('--val', type=str, default='ml/data/processed/validation.jsonl', help="Validation JSONL path")
    parser.add_argument('--test', type=str, default='ml/data/processed/test.jsonl', help="Test JSONL path")
    parser.add_argument('--output', type=str, default='ml/data/processed/dataset_statistics.json', help="Output stats JSON")
    args = parser.parse_args()

    compute_statistics(
        raw_path=args.raw,
        cleaned_path=args.cleaned,
        rejected_path=args.rejected,
        train_path=args.train,
        val_path=args.val,
        test_path=args.test,
        output_json=args.output
    )
