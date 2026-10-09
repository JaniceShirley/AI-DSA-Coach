from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAIProvider(ABC):
    """
    Abstract base class for AI Model Providers (Open-source LLMs, OpenAI-compatible APIs, Mock, QLoRA endpoints).
    Ensures the underlying model/provider can be swapped via environment variables without changing app logic.
    """

    @abstractmethod
    def generate_hint(self, context: Dict[str, Any]) -> str:
        """Generate progressive hint (Levels 1-4) based on problem and student context."""
        pass

    @abstractmethod
    def challenge_understanding(self, context: Dict[str, Any]) -> str:
        """Generate follow-up conceptual/edge-case challenge questions or evaluate student answers."""
        pass

    @abstractmethod
    def generate_alternative_approach(self, context: Dict[str, Any]) -> str:
        """Explain alternative valid algorithmic approaches, trade-offs, and complexities."""
        pass

    @abstractmethod
    def generate_feedback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured feedback evaluating approach, correctness, time/space complexity, edge cases, and optimization."""
        pass

    @abstractmethod
    def conduct_interview_turn(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct an interactive technical interview turn, returning message, current stage, and next action."""
        pass

    @abstractmethod
    def evaluate_interview(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate overall mock technical interview performance across all rubric categories."""
        pass

    @abstractmethod
    def conduct_chat_turn(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct a conversational DSA reasoning coaching turn."""
        pass
