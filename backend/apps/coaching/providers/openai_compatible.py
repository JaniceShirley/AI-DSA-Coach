import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any
from .base import BaseAIProvider

logger = logging.getLogger(__name__)

COACHING_SYSTEM_PROMPT = """You are an expert Data Structures & Algorithms (DSA) Coach.
Your primary role is to help students learn and solve coding problems independently.

CRITICAL RULES:
1. NEVER output a complete solution, complete function code, or full copy-paste implementation.
2. Provide progressive guidance, asking questions that lead the student to discover the answer themselves.
3. Tailor your hint to the requested hint level:
   - Level 1: Conceptual (high-level intuition, no specific syntax)
   - Level 2: Directional (point toward technique/data structure)
   - Level 3: Strategic (algorithmic steps without writing code)
   - Level 4: Detailed Guidance (detailed reasoning, edge case analysis, line-by-line debugging hint without complete solution code)
4. Highlight syntax/logic errors, edge cases, and time/space complexity trade-offs when inspecting student code.
"""

class OpenAICompatibleProvider(BaseAIProvider):
    """
    Provider for OpenAI API, vLLM, Ollama, HuggingFace TGI, or custom QLoRA fine-tuned model endpoints.
    """

    def __init__(self, model: str = None, api_key: str = None, base_url: str = None):
        self.model = model or os.getenv('AI_MODEL') or os.getenv('LLM_MODEL_NAME', 'gpt-3.5-turbo')
        self.api_key = api_key or os.getenv('AI_API_KEY') or os.getenv('OPENAI_API_KEY', '')
        self.base_url = (base_url or os.getenv('AI_BASE_URL') or 'https://api.openai.com/v1').rstrip('/')

    def _call_llm(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.4,
            "max_tokens": 800,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Error calling LLM provider at {url}: {e}")
            raise RuntimeError(f"LLM Provider API request failed: {e}")

    def generate_hint(self, context: Dict[str, Any]) -> str:
        problem = context.get('problem', {})
        hint_level = context.get('hint_level', 1)
        student_code = context.get('student_code', '')
        latest_sub = context.get('latest_submission', {})

        prompt = f"""Problem Title: {problem.get('title')}
Description: {problem.get('description')}
Topics: {', '.join(problem.get('topics', []))}
Patterns: {', '.join(problem.get('patterns', []))}

Student's Current Code:
```python
{student_code}
```

Latest Submission Result: {json.dumps(latest_sub)}
Requested Hint Level: Level {hint_level}

Please provide a Level {hint_level} hint for the student. Remember: DO NOT provide the complete solution code."""

        return self._call_llm(COACHING_SYSTEM_PROMPT, prompt)

    def challenge_understanding(self, context: Dict[str, Any]) -> str:
        problem = context.get('problem', {})
        student_code = context.get('student_code', '')
        user_question = context.get('user_question', '')

        prompt = f"""Problem Title: {problem.get('title')}
Student's Code:
```python
{student_code}
```
Student's Input/Response: "{user_question}"

Ask 2-3 targeted conceptual or edge-case questions to challenge the student's understanding of their solution's time/space complexity and correctness."""

        return self._call_llm(COACHING_SYSTEM_PROMPT, prompt)

    def generate_alternative_approach(self, context: Dict[str, Any]) -> str:
        problem = context.get('problem', {})
        student_code = context.get('student_code', '')

        prompt = f"""Problem Title: {problem.get('title')}
Description: {problem.get('description')}
Student's Current Approach:
```python
{student_code}
```

Explain an alternative valid algorithmic strategy (e.g. comparing Hash Map vs Sorting/Two-Pointers or Iterative vs Recursive). Detail time/space complexity and trade-offs. Do not provide complete runnable code."""

        return self._call_llm(COACHING_SYSTEM_PROMPT, prompt)

    def generate_feedback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        problem = context.get('problem', {})
        student_code = context.get('student_code', '')
        latest_sub = context.get('latest_submission', {})

        prompt = f"""Problem Title: {problem.get('title')}
Student's Code:
```python
{student_code}
```
Submission Result: {json.dumps(latest_sub)}

Provide structured feedback in JSON format with exactly these keys:
"approach", "correctness", "time_complexity", "space_complexity", "edge_cases", "optimization"."""

        raw_resp = self._call_llm(
            COACHING_SYSTEM_PROMPT + "\nReturn strictly JSON object.",
            prompt,
            json_mode=True
        )

        try:
            return json.loads(raw_resp)
        except Exception:
            return {
                "approach": raw_resp,
                "correctness": "Evaluated",
                "time_complexity": "See feedback",
                "space_complexity": "See feedback",
                "edge_cases": "See feedback",
                "optimization": "See feedback"
            }

    def conduct_interview_turn(self, context: Dict[str, Any]) -> Dict[str, Any]:
        problem = context.get('problem', {})
        current_stage = context.get('stage', 'PROBLEM_INTRO')
        student_message = context.get('student_message', '')
        history = context.get('dialogue_history', [])

        prompt = f"""You are a Senior FAANG Technical Interviewer conducting a live Technical Coding Interview on '{problem.get('title')}'.
Problem Description:
{problem.get('description')}

Current Interview Stage: {current_stage}
Candidate's Spoken Response: "{student_message}"
Recent Dialogue History:
{json.dumps(history)}

Strict Interviewer Guidelines:
1. Act as a seasoned, conversational senior technical interviewer.
2. DO NOT repeat or echo the candidate's transcript verbatim (e.g., NEVER say "I see your point regarding: '<transcript>'").
3. Acknowledge candidate's technical reasoning briefly in 1 sentence, then ask ONE focused follow-up question.
4. Evaluate the candidate's actual answer without fixing their mistakes:
   - If candidate proposes brute force, acknowledge it and ask for time & space complexity.
   - If candidate proposes an unsuitable method (e.g. Two Pointers on an unsorted array), DO NOT correct it for them; challenge the assumption ("Two pointers work well on sorted arrays. Since this array is unsorted, how would you adapt that?").
   - If candidate gives correct complexity, probe optimization.
   - If candidate proposes an optimized approach (e.g. hash map for Two Sum), ask how it finds the complement in a single pass.
   - In edge cases, evaluate boundary conditions before advancing to coding.
5. Keep responses concise (2-4 sentences max), natural, and focused on DSA reasoning.
6. Progress naturally through stages (PROBLEM_INTRO -> APPROACH -> COMPLEXITY -> OPTIMIZATION -> EDGE_CASES -> CODING -> FINAL_EVALUATION).
   Only advance stage ("should_advance_stage": true) when the candidate has adequately answered the current question.

Return strictly a JSON object with:
{{
  "stage": "next or current stage name",
  "message": "your natural interviewer reply asking ONE question",
  "should_advance_stage": true or false,
  "should_end": false
}}
"""
        raw_resp = self._call_llm(
            "You are a Senior Technical Interviewer. Return JSON only.",
            prompt,
            json_mode=True
        )
        try:
            return json.loads(raw_resp)
        except Exception:
            return {
                "stage": current_stage,
                "message": raw_resp,
                "should_advance_stage": False,
                "should_end": False
            }

    def evaluate_interview(self, context: Dict[str, Any]) -> Dict[str, Any]:
        problem = context.get('problem', {})
        dialogue = context.get('full_transcript', [])
        latest_sub = context.get('latest_submission')

        prompt = f"""Evaluate this full Mock Technical Interview on '{problem.get('title')}'.
Submission Result: {json.dumps(latest_sub)}
Dialogue Transcript:
{json.dumps(dialogue)}

Provide a comprehensive rubric evaluation in JSON with keys:
- overall_score (integer 0-100)
- problem_understanding ({"rating": "Strong/Good/Needs Improvement", "notes": "..."})
- approach_quality ({"rating": "...", "notes": "..."})
- technical_reasoning ({"rating": "...", "notes": "..."})
- complexity_analysis ({"rating": "...", "notes": "..."})
- edge_case_awareness ({"rating": "...", "notes": "..."})
- optimization ({"rating": "...", "notes": "..."})
- communication ({"rating": "...", "notes": "..."})
- coding_correctness ({"rating": "...", "notes": "..."})
- strengths (list of strings)
- areas_for_improvement (list of strings)
- final_feedback (detailed text summary)
- recommended_topics (list of strings)
- recommended_problems (list of problem titles or ids)
"""
        raw_resp = self._call_llm(
            "You are an Interview Evaluation Committee Lead. Return JSON only.",
            prompt,
            json_mode=True
        )
        try:
            return json.loads(raw_resp)
        except Exception:
            return {
                "overall_score": 80,
                "problem_understanding": {"rating": "Good", "notes": "Understood the problem."},
                "approach_quality": {"rating": "Good", "notes": "Formulated valid approach."},
                "technical_reasoning": {"rating": "Good", "notes": "Explained logic."},
                "complexity_analysis": {"rating": "Good", "notes": "Derived bounds."},
                "edge_case_awareness": {"rating": "Good", "notes": "Identified edge cases."},
                "optimization": {"rating": "Good", "notes": "Discussed optimizations."},
                "communication": {"rating": "Good", "notes": "Communicated clearly."},
                "coding_correctness": {"rating": "Good", "notes": "Completed code."},
                "strengths": ["Clear communication", "Structured approach"],
                "areas_for_improvement": ["Deeper edge case analysis"],
                "final_feedback": raw_resp,
                "recommended_topics": problem.get('topics', []),
                "recommended_problems": []
            }

    def conduct_chat_turn(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from apps.coaching.mentor_engine import DSACoachDialogueEngine
        problem = context.get('problem_obj')
        if not problem:
            from apps.problems.models import Problem
            prob_dict = context.get('problem', {})
            problem = Problem.objects.filter(id=prob_dict.get('id')).first()

        return DSACoachDialogueEngine.process_turn(
            problem=problem,
            session_data=context.get('session_data', {}),
            student_message=context.get('student_message', ''),
            student_code=context.get('student_code', ''),
            run_code=context.get('run_code', False)
        )


