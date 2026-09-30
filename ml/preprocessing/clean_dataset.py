import os
import sys
import json
import re
import argparse
from typing import Dict, Any, List, Tuple

def normalize_text(text: str) -> str:
    """Normalize whitespace and line endings."""
    if not text:
        return ""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def check_solution_leakage(text: str, hint_level: Any) -> Tuple[bool, str]:
    """
    Rule 5: Detect solution leakage where the coach reveals full implementations prematurely.
    """
    if not text:
        return False, ""
    
    # Check for complete function definitions with return statements (supports type annotations -> ...)
    has_def = bool(re.search(r'def\s+\w+\s*\([^)]*\)\s*(?:->[^:]+)?\s*:', text))
    has_return = 'return ' in text

    # Check for markdown code blocks
    code_blocks = re.findall(r'```(?:python|py)?([\s\S]*?)```', text)
    for block in code_blocks:
        lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
        # Full function block with return statement
        if has_def and has_return and len(lines) >= 5:
            if hint_level in (1, 2, 3) or hint_level is None:
                return True, "Code block contains complete function definition with return statement."

    # Direct function definition in early hints (level 1 or 2)
    if hint_level in (1, 2) and has_def and has_return:
        return True, f"Early hint level {hint_level} contains runnable function definition with return."

    return False, ""

def validate_and_clean_record(record: Dict[str, Any], seen_keys: set) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validates and cleans an interaction record according to documented rules:
    - Rule 1: Missing-field handling (problem metadata, responses, student context)
    - Rule 2: Problem metadata validation (valid difficulty, topics, description)
    - Rule 3: Interaction type validation (hint, challenge, alternative, feedback, interview)
    - Rule 4: Empty & ultra-short response detection (< 15 chars)
    - Rule 5: Solution leakage detection for early hints
    - Rule 6: Duplicate detection (exact normalized prompt-response pairs)
    - Rule 7: Text normalization
    """
    reasons = []
    cleaned = dict(record)

    # Rule 3: Interaction type validation
    interaction_type = str(record.get('interaction_type', '')).lower()
    valid_types = {'hint', 'challenge', 'alternative', 'feedback', 'interview'}
    if interaction_type not in valid_types:
        reasons.append(f"INVALID_INTERACTION_TYPE: '{interaction_type}' not in {valid_types}")

    # Determine user prompt and coach response fields based on interaction type
    if interaction_type == 'interview':
        coach_resp = normalize_text(record.get('interviewer_response', ''))
        student_input = normalize_text(record.get('student_response', ''))
        student_code = normalize_text(record.get('student_code', ''))
    else:
        coach_resp = normalize_text(record.get('coach_response', ''))
        student_input = normalize_text(record.get('student_question', ''))
        student_code = normalize_text(record.get('student_code', ''))

    hint_level = record.get('hint_level')
    if hint_level is not None:
        try:
            hint_level = int(hint_level)
            cleaned['hint_level'] = hint_level
        except (ValueError, TypeError):
            reasons.append(f"INVALID_HINT_LEVEL: '{hint_level}' is not an integer")

    # Rule 4: Empty and ultra-short response removal
    if not coach_resp:
        reasons.append("EMPTY_RESPONSE: Coach/Interviewer response is empty")
    elif len(coach_resp) < 15:
        reasons.append(f"EXTREMELY_SHORT_RESPONSE: Length {len(coach_resp)} < 15 chars ('{coach_resp}')")

    # Rule 1: Missing context
    if not student_input and not student_code:
        reasons.append("MISSING_STUDENT_CONTEXT: Both student question/response and student code are empty")

    # Rule 2: Problem metadata validation
    prob_id = record.get('problem_id')
    prob_title = normalize_text(record.get('problem_title', ''))
    prob_desc = normalize_text(record.get('problem_description', ''))
    difficulty = str(record.get('difficulty', '')).strip().lower()

    if not prob_id or not prob_title:
        reasons.append("MISSING_PROBLEM: Missing problem_id or problem_title")
    if not prob_desc:
        reasons.append("MISSING_PROBLEM_DESCRIPTION: Problem description is empty")
    if difficulty not in ('easy', 'medium', 'hard'):
        reasons.append(f"INVALID_DIFFICULTY: '{difficulty}' not in (easy, medium, hard)")

    # Rule 5: Solution leakage
    is_leak, leak_desc = check_solution_leakage(coach_resp, hint_level)
    if is_leak:
        reasons.append(f"COMPLETE_CODE_LEAKAGE: {leak_desc}")

    # Rule 6: Duplicate detection
    dedup_key = (
        prob_id,
        interaction_type,
        hint_level,
        student_input[:100],
        student_code[:100],
        coach_resp[:100]
    )
    if dedup_key in seen_keys:
        reasons.append("DUPLICATE_RECORD: Identical interaction pattern already exists in dataset")
    else:
        seen_keys.add(dedup_key)

    # Normalize fields in cleaned record
    cleaned['problem_title'] = prob_title
    cleaned['problem_description'] = prob_desc
    cleaned['difficulty'] = difficulty
    if interaction_type == 'interview':
        cleaned['interviewer_response'] = coach_resp
        cleaned['student_response'] = student_input
    else:
        cleaned['coach_response'] = coach_resp
        cleaned['student_question'] = student_input
        cleaned['student_code'] = student_code

    if reasons:
        cleaned['validation_status'] = 'REJECTED'
        cleaned['quality_status'] = f"FLAGGED_{reasons[0].split(':')[0]}"
        cleaned['rejection_reasons'] = reasons
        return False, reasons, cleaned
    else:
        cleaned['validation_status'] = 'APPROVED'
        cleaned['quality_status'] = 'PASSED_CLEANING_PIPELINE'
        cleaned['rejection_reasons'] = []
        return True, [], cleaned

def clean_dataset(input_file: str, output_file: str, rejected_file: str):
    """Clean the raw interactions dataset and output approved & rejected files."""
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file {input_file} does not exist.")

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(rejected_file)), exist_ok=True)

    seen_keys = set()
    total = 0
    approved_count = 0
    rejected_count = 0
    rejection_summary = {}

    with open(input_file, 'r', encoding='utf-8') as fin, \
         open(output_file, 'w', encoding='utf-8') as fout, \
         open(rejected_file, 'w', encoding='utf-8') as frej:

        for line_num, line in enumerate(fin, start=1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                rejected_count += 1
                rej_rec = {
                    "raw_line": line,
                    "validation_status": "REJECTED",
                    "quality_status": "INVALID_JSON",
                    "rejection_reasons": [f"INVALID_JSON: {str(e)}"]
                }
                frej.write(json.dumps(rej_rec, ensure_ascii=False) + '\n')
                continue

            is_valid, reasons, processed = validate_and_clean_record(record, seen_keys)
            if is_valid:
                approved_count += 1
                fout.write(json.dumps(processed, ensure_ascii=False) + '\n')
            else:
                rejected_count += 1
                frej.write(json.dumps(processed, ensure_ascii=False) + '\n')
                for r in reasons:
                    cat = r.split(':')[0]
                    rejection_summary[cat] = rejection_summary.get(cat, 0) + 1

    print(f"==================================================")
    print(f"DATA CLEANING COMPLETED")
    print(f"==================================================")
    print(f"Total raw records processed: {total}")
    print(f"Approved (Cleaned) records:  {approved_count} ({approved_count/total*100:.1f}%)")
    print(f"Rejected records:            {rejected_count} ({rejected_count/total*100:.1f}%)")
    print(f"Rejection breakdown:")
    for cat, cnt in sorted(rejection_summary.items(), key=lambda x: -x[1]):
        print(f"  - {cat}: {cnt}")
    print(f"Cleaned output:  {output_file}")
    print(f"Rejected output: {rejected_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Clean raw AI coaching interactions.")
    parser.add_argument('--input', type=str, default='ml/data/raw/raw_interactions.jsonl', help="Input raw JSONL file")
    parser.add_argument('--output', type=str, default='ml/data/processed/cleaned_interactions.jsonl', help="Output cleaned JSONL file")
    parser.add_argument('--rejected', type=str, default='ml/data/processed/rejected_interactions.jsonl', help="Output rejected JSONL file")
    args = parser.parse_args()

    clean_dataset(args.input, args.output, args.rejected)
