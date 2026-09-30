import os
import json
import argparse
from typing import Dict, Any, List

SYSTEM_PROMPTS = {
    "hint": (
        "You are an AI DSA Coach specializing in progressive, Socratic guidance. "
        "Your mission is to help students learn data structures and algorithms by providing targeted hints matched to the requested hint level. "
        "Strict rules: Never output full, copy-pasteable solutions or complete function definitions. "
        "Level 1: Focus on problem intuition, invariants, and conceptual understanding. "
        "Level 2: Directional guidance toward optimal data structures and algorithmic patterns. "
        "Level 3: Strategic step-by-step logic, state transitions, and edge cases. "
        "Level 4: Detailed pseudocode or implementation checkpoints without writing the complete solution."
    ),
    "challenge": (
        "You are an AI DSA Coach testing the student's algorithmic mastery and critical thinking. "
        "Analyze the student's code and proposed logic. Ask rigorous Socratic questions about worst-case time/space complexity, "
        "subtle edge cases (empty inputs, duplicates, integer overflows, extreme constraints), and algorithmic trade-offs."
    ),
    "alternative": (
        "You are an AI DSA Coach explaining alternative algorithmic paradigms. "
        "Compare multiple valid approaches (e.g., Hash Map vs Sorting + Two Pointers, Iterative vs Recursive/DP). "
        "Provide thorough time/space complexity comparisons and practical engineering trade-offs."
    ),
    "feedback": (
        "You are an AI DSA Coach providing constructive code feedback. "
        "Evaluate student code for correctness, time complexity, space complexity, edge-case coverage, and idiomatic clean code practices. "
        "Highlight strengths, explain potential bugs or bottlenecks, and guide the student toward optimization."
    ),
    "interview": (
        "You are a professional AI Technical Interviewer conducting a rigorous DSA mock interview. "
        "Assess candidate problem understanding, approach justification, complexity analysis, edge-case awareness, and communication. "
        "Respond constructively to candidate dialogue turns, challenge assumptions, and guide the candidate to articulate their reasoning."
    )
}

HINT_LEVEL_DESCRIPTIONS = {
    1: "Level 1 (Conceptual Intuition)",
    2: "Level 2 (Directional & Data Structure Selection)",
    3: "Level 3 (Strategic Logic & State Transition)",
    4: "Level 4 (Detailed Pseudocode & Edge Cases)"
}

def format_user_prompt(record: Dict[str, Any]) -> str:
    """Formats student context, problem metadata, and question into a structured user prompt."""
    interaction_type = record.get('interaction_type', 'hint')
    prob_title = record.get('problem_title', '')
    difficulty = record.get('difficulty', '')
    topics = record.get('topic', [])
    topic_str = ", ".join(topics) if isinstance(topics, list) else str(topics)
    desc = record.get('problem_description', '')

    parts = [
        f"[PROBLEM CONTEXT]",
        f"Title: {prob_title}",
        f"Difficulty: {difficulty.capitalize()}",
        f"Topics: {topic_str}",
        f"Description:\n{desc}"
    ]

    if interaction_type == 'interview':
        stage = record.get('stage', 'APPROACH')
        student_resp = record.get('student_response', '')
        parts.append(f"\n[INTERVIEW STAGE]\nStage: {stage}")
        parts.append(f"\n[CANDIDATE RESPONSE]\n{student_resp}")
    else:
        student_code = record.get('student_code', '').strip()
        student_q = record.get('student_question', '').strip()
        hint_level = record.get('hint_level')

        if student_code:
            parts.append(f"\n[STUDENT CODE]\n```python\n{student_code}\n```")

        if student_q:
            parts.append(f"\n[STUDENT QUESTION]\n{student_q}")

        task_desc = f"Task: {interaction_type}"
        if hint_level:
            level_str = HINT_LEVEL_DESCRIPTIONS.get(int(hint_level), f"Level {hint_level}")
            task_desc += f" | Requested: {level_str}"
        parts.append(f"\n[COACHING OBJECTIVE]\n{task_desc}")

    return "\n".join(parts)

def format_record_for_qlora(record: Dict[str, Any]) -> Dict[str, Any]:
    """Converts a cleaned record into a Hugging Face / TRL chat-format example."""
    interaction_type = record.get('interaction_type', 'hint')
    system_prompt = SYSTEM_PROMPTS.get(interaction_type, SYSTEM_PROMPTS['hint'])
    user_prompt = format_user_prompt(record)

    if interaction_type == 'interview':
        assistant_response = record.get('interviewer_response', '')
    else:
        assistant_response = record.get('coach_response', '')

    return {
        "id": record.get("id"),
        "interaction_type": interaction_type,
        "hint_level": record.get("hint_level"),
        "problem_id": record.get("problem_id"),
        "problem_slug": record.get("problem_slug"),
        "difficulty": record.get("difficulty"),
        "session_id": record.get("session_id"),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_response}
        ]
    }

def format_dataset(input_file: str, output_file: str):
    """Transform cleaned records into chat-formatted QLoRA dataset."""
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file {input_file} not found.")

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    count = 0

    with open(input_file, 'r', encoding='utf-8') as fin, \
         open(output_file, 'w', encoding='utf-8') as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            formatted = format_record_for_qlora(record)
            fout.write(json.dumps(formatted, ensure_ascii=False) + '\n')
            count += 1

    print(f"Successfully formatted {count} examples into QLoRA chat format at {output_file}.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Format cleaned dataset into Hugging Face/TRL QLoRA format.")
    parser.add_argument('--input', type=str, default='ml/data/processed/cleaned_interactions.jsonl', help="Input cleaned JSONL")
    parser.add_argument('--output', type=str, default='ml/data/processed/qlora_formatted.jsonl', help="Output formatted JSONL")
    args = parser.parse_args()

    format_dataset(args.input, args.output)
