import os
import logging
from typing import Dict, Any, Optional
from .base import BaseAIProvider
from .mock import MockAIProvider

logger = logging.getLogger(__name__)

class DSACoachModel(BaseAIProvider):
    """
    Unified AI DSA Coach Model Provider supporting:
    - FINE_TUNED_MODEL mode (QLoRA LoRA adapter attached)
    - BASE_MODEL mode (Direct zero-shot inference without adapter)
    - MOCK / API FALLBACK mode (Graceful fallback if weights not present or during test runs)

    Environment variables:
    - AI_MODEL_BACKEND: 'finetuned', 'base', 'mock' (also checks COACH_MODEL_MODE)
    - BASE_MODEL_NAME: default 'Qwen/Qwen2.5-Coder-0.5B-Instruct'
    - LORA_ADAPTER_PATH: default 'ml/models/adapters/dsa-coach-lora'
    """

    _CACHED_ENGINES: Dict[str, Any] = {}

    def __init__(
        self,
        mode: Optional[str] = None,
        base_model_name: Optional[str] = None,
        adapter_path: Optional[str] = None
    ):
        raw_mode = mode or os.getenv("AI_MODEL_BACKEND") or os.getenv("COACH_MODEL_MODE", "mock")
        # Normalize: 'finetuned' / 'fine_tuned' -> 'finetuned'
        norm_mode = raw_mode.lower().replace("_", "").replace("-", "")
        if "fine" in norm_mode:
            self.mode = "finetuned"
        elif "base" in norm_mode:
            self.mode = "base"
        else:
            self.mode = "mock"

        self.base_model_name = base_model_name or os.getenv("BASE_MODEL_NAME", "Qwen/Qwen2.5-Coder-0.5B-Instruct")
        self.adapter_path = adapter_path or os.getenv("LORA_ADAPTER_PATH", "ml/models/adapters/dsa-coach-lora")
        self.fallback = MockAIProvider()

    def get_mode_info(self) -> Dict[str, Any]:
        """Returns human-readable and development metadata about the current model configuration."""
        return {
            "mode": self.mode,
            "base_model": self.base_model_name,
            "adapter_path": self.adapter_path if self.mode == "finetuned" else None,
            "is_fine_tuned": self.mode == "finetuned",
            "model_version": "dsa-coach-qlora-v1"
        }

    def _get_inference_engine(self):
        """Persistent singleton loader for local PyTorch/Transformers inference engine."""
        cache_key = f"{self.mode}_{self.base_model_name}_{self.adapter_path}"
        if cache_key in DSACoachModel._CACHED_ENGINES:
            return DSACoachModel._CACHED_ENGINES[cache_key]

        try:
            from ml.inference.run_model import DSACoachInference
            use_adapter = (self.mode == "finetuned")
            engine = DSACoachInference(
                base_model_name=self.base_model_name,
                adapter_path=self.adapter_path,
                use_adapter=use_adapter,
                load_in_4bit=True
            )
            DSACoachModel._CACHED_ENGINES[cache_key] = engine
            return engine
        except Exception as e:
            logger.warning(f"Could not initialize local DSACoachInference ({cache_key}): {e}. Using fallback provider.")
            return None

    def generate_hint(self, context: Dict[str, Any]) -> str:
        if self.mode == "mock":
            return self.fallback.generate_hint(context)

        try:
            engine = self._get_inference_engine()
            if not engine:
                return self.fallback.generate_hint(context)

            prob = context.get("problem", {})
            prompt = engine.format_prompt(
                problem_title=prob.get("title", ""),
                difficulty=prob.get("difficulty", "Easy"),
                topics=prob.get("topics", []),
                description=prob.get("description", ""),
                student_code=context.get("student_code", ""),
                student_question=context.get("user_question", ""),
                hint_level=context.get("hint_level", 1),
                interaction_type="hint"
            )
            return engine.generate(prompt)
        except Exception as e:
            logger.error(f"Error in DSACoachModel.generate_hint: {e}. Executing fallback.")
            return self.fallback.generate_hint(context)

    def challenge_understanding(self, context: Dict[str, Any]) -> str:
        if self.mode == "mock":
            return self.fallback.challenge_understanding(context)

        try:
            engine = self._get_inference_engine()
            if not engine:
                return self.fallback.challenge_understanding(context)

            prob = context.get("problem", {})
            prompt = engine.format_prompt(
                problem_title=prob.get("title", ""),
                difficulty=prob.get("difficulty", "Easy"),
                topics=prob.get("topics", []),
                description=prob.get("description", ""),
                student_code=context.get("student_code", ""),
                student_question=context.get("user_question", ""),
                interaction_type="challenge"
            )
            return engine.generate(prompt)
        except Exception as e:
            logger.error(f"Error in DSACoachModel.challenge_understanding: {e}. Executing fallback.")
            return self.fallback.challenge_understanding(context)

    def generate_alternative_approach(self, context: Dict[str, Any]) -> str:
        if self.mode == "mock":
            return self.fallback.generate_alternative_approach(context)

        try:
            engine = self._get_inference_engine()
            if not engine:
                return self.fallback.generate_alternative_approach(context)

            prob = context.get("problem", {})
            prompt = engine.format_prompt(
                problem_title=prob.get("title", ""),
                difficulty=prob.get("difficulty", "Easy"),
                topics=prob.get("topics", []),
                description=prob.get("description", ""),
                student_code=context.get("student_code", ""),
                student_question=context.get("user_question", ""),
                interaction_type="alternative"
            )
            return engine.generate(prompt)
        except Exception as e:
            logger.error(f"Error in DSACoachModel.generate_alternative_approach: {e}. Executing fallback.")
            return self.fallback.generate_alternative_approach(context)

    def generate_feedback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured code feedback evaluating student code correctness and complexity."""
        if self.mode == "mock":
            return self.fallback.generate_feedback(context)

        try:
            engine = self._get_inference_engine()
            if not engine:
                return self.fallback.generate_feedback(context)

            prob = context.get("problem", {})
            student_code = context.get("student_code", "")
            prompt = engine.format_prompt(
                problem_title=prob.get("title", ""),
                difficulty=prob.get("difficulty", "Easy"),
                topics=prob.get("topics", []),
                description=prob.get("description", ""),
                student_code=student_code,
                student_question="Please provide code feedback on correctness and efficiency.",
                interaction_type="feedback"
            )
            raw_feedback = engine.generate(prompt)
            # Combine generated feedback with structured evaluation schema
            feedback = self.fallback.generate_feedback(context)
            if raw_feedback and len(raw_feedback) > 20:
                feedback["optimization"] = raw_feedback
            return feedback
        except Exception as e:
            logger.error(f"Error in DSACoachModel.generate_feedback: {e}. Executing fallback.")
            return self.fallback.generate_feedback(context)

    def conduct_interview_turn(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct technical mock interview dialogue turn."""
        if self.mode == "mock":
            return self.fallback.conduct_interview_turn(context)

        try:
            engine = self._get_inference_engine()
            if not engine:
                return self.fallback.conduct_interview_turn(context)

            prob = context.get("problem", {})
            stage = context.get("stage", "APPROACH")
            student_msg = context.get("student_message", "")
            prompt = engine.format_prompt(
                problem_title=prob.get("title", ""),
                difficulty=prob.get("difficulty", "Easy"),
                topics=prob.get("topics", []),
                description=prob.get("description", ""),
                student_code="",
                student_question=student_msg,
                interaction_type="interview",
                stage=stage
            )
            response_msg = engine.generate(prompt)
            # Default stage transition logic
            result = self.fallback.conduct_interview_turn(context)
            if response_msg and len(response_msg) > 15:
                result["message"] = response_msg
            return result
        except Exception as e:
            logger.error(f"Error in DSACoachModel.conduct_interview_turn: {e}. Executing fallback.")
            return self.fallback.conduct_interview_turn(context)

    def evaluate_interview(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.fallback.evaluate_interview(context)

    def conduct_chat_turn(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.fallback.conduct_chat_turn(context)

