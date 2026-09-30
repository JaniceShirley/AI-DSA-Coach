import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

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

class DSACoachInference:
    """
    Inference interface for running Base Model and Fine-Tuned LoRA Adapter.
    Preserves base model weights and allows dynamic switching.
    """

    def __init__(
        self,
        base_model_name: str = "Qwen/Qwen2.5-Coder-0.5B-Instruct",
        adapter_path: Optional[str] = "ml/models/adapters/dsa-coach-lora",
        use_adapter: bool = True,
        load_in_4bit: bool = True
    ):
        self.base_model_name = base_model_name
        self.adapter_path = adapter_path
        self.use_adapter = use_adapter and (adapter_path is not None and os.path.exists(adapter_path))

        print(f"Loading tokenizer for: {base_model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            adapter_path if (self.use_adapter and os.path.exists(os.path.join(adapter_path, "tokenizer_config.json"))) else base_model_name,
            trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        print(f"Loading base model (4-bit: {load_in_4bit})...")
        compute_dtype = torch.float32 if not torch.cuda.is_available() else torch.bfloat16
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=load_in_4bit,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=compute_dtype
        ) if load_in_4bit else None

        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )

        if self.use_adapter:
            print(f"Attaching LoRA adapter from: {adapter_path}...")
            self.model = PeftModel.from_pretrained(self.model, adapter_path)
            self.model.eval()
            print("Fine-tuned LoRA adapter attached successfully.")
        else:
            self.model.eval()
            print("Operating in BASE MODEL mode (no adapter attached).")

    def format_prompt(
        self,
        problem_title: str,
        difficulty: str = "Easy",
        topics: Any = None,
        description: str = "",
        student_code: str = "",
        student_question: str = "",
        hint_level: Optional[int] = 1,
        interaction_type: str = "hint",
        stage: str = "APPROACH"
    ) -> str:
        """Constructs chat template message list formatted with system, user, and assistant prompt."""
        topic_str = ", ".join(topics) if isinstance(topics, list) else str(topics or "")
        system_content = SYSTEM_PROMPTS.get(interaction_type, SYSTEM_PROMPTS["hint"])

        parts = [
            f"[PROBLEM CONTEXT]",
            f"Title: {problem_title}",
            f"Difficulty: {str(difficulty).capitalize()}",
            f"Topics: {topic_str}",
            f"Description:\n{description}"
        ]

        if interaction_type == "interview":
            parts.append(f"\n[INTERVIEW STAGE]\nStage: {stage}")
            parts.append(f"\n[CANDIDATE RESPONSE]\n{student_question}")
        else:
            if student_code:
                parts.append(f"\n[STUDENT CODE]\n```python\n{student_code}\n```")
            if student_question:
                parts.append(f"\n[STUDENT QUESTION]\n{student_question}")

            task_desc = f"Task: {interaction_type}"
            if hint_level:
                level_str = HINT_LEVEL_DESCRIPTIONS.get(int(hint_level), f"Level {hint_level}")
                task_desc += f" | Requested: {level_str}"
            parts.append(f"\n[COACHING OBJECTIVE]\n{task_desc}")

        user_content = "\n".join(parts)
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

    def generate(
        self,
        formatted_prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.3,
        top_p: float = 0.9
    ) -> str:
        """Generates model response text from formatted chat prompt."""
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)
        input_len = inputs["input_ids"].shape[1]

        with torch.no_grad():
            output_tokens = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature if temperature > 0 else None,
                top_p=top_p if temperature > 0 else None,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        gen_tokens = output_tokens[0][input_len:]
        response_text = self.tokenizer.decode(gen_tokens, skip_special_tokens=True)
        return response_text.strip()

def main():
    parser = argparse.ArgumentParser(description="Run inference with Base Model or Fine-Tuned LoRA Adapter.")
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-Coder-0.5B-Instruct", help="Base model identifier")
    parser.add_argument("--adapter", type=str, default="ml/models/adapters/dsa-coach-lora", help="Path to LoRA adapter")
    parser.add_argument("--no_adapter", action="store_true", help="Run base model without LoRA adapter")
    parser.add_argument("--problem", type=str, default="Two Sum", help="Problem title")
    parser.add_argument("--difficulty", type=str, default="Easy", help="Problem difficulty")
    parser.add_argument("--question", type=str, default="My solution is too slow for large arrays. How can I improve it?", help="Student question")
    parser.add_argument("--code", type=str, default="def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target: return [i, j]", help="Student code")
    parser.add_argument("--hint_level", type=int, default=1, help="Requested hint level (1-4)")
    parser.add_argument("--type", type=str, default="hint", help="Interaction type (hint, challenge, alternative, feedback, interview)")
    parser.add_argument("--max_tokens", type=int, default=256, help="Max new tokens")
    args = parser.parse_args()

    use_adapter = not args.no_adapter
    coach = DSACoachInference(
        base_model_name=args.base_model,
        adapter_path=args.adapter,
        use_adapter=use_adapter
    )

    prompt = coach.format_prompt(
        problem_title=args.problem,
        difficulty=args.difficulty,
        student_code=args.code,
        student_question=args.question,
        hint_level=args.hint_level,
        interaction_type=args.type
    )

    mode_label = "FINE-TUNED QLoRA MODEL" if coach.use_adapter else "BASE MODEL (Zero-Shot)"
    print(f"\n=== Generating response using {mode_label} ===")
    response = coach.generate(prompt, max_new_tokens=args.max_tokens)
    print("\n--- COACH RESPONSE ---")
    print(response)
    print("----------------------\n")

if __name__ == "__main__":
    main()
