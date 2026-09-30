import os
import logging
from .base import BaseAIProvider
from .mock import MockAIProvider
from .openai_compatible import OpenAICompatibleProvider
from .dsa_coach_model import DSACoachModel

logger = logging.getLogger(__name__)

def get_ai_provider() -> BaseAIProvider:
    """
    Factory function returning the configured AI Provider based on environment variables:
    - AI_PROVIDER (or LLM_PROVIDER): 'mock', 'openai', 'openai-compatible', 'ollama', 'qlora', 'dsa_coach'
    - COACH_MODEL_MODE: 'fine_tuned', 'base', 'mock'
    """
    provider_type = (os.getenv('AI_PROVIDER') or os.getenv('LLM_PROVIDER') or 'mock').lower()
    backend_mode = (os.getenv('AI_MODEL_BACKEND') or '').lower()

    # If explicit AI_MODEL_BACKEND is set (finetuned/base) or AI_PROVIDER is dsa_coach/qlora
    if backend_mode in ('finetuned', 'fine_tuned', 'base') or provider_type in ('dsa_coach', 'qlora', 'local_qlora'):
        return DSACoachModel()

    if provider_type in ('openai', 'openai-compatible', 'ollama', 'vllm'):
        api_key = os.getenv('AI_API_KEY') or os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('AI_BASE_URL')
        
        # If no API key or base URL for external provider, log warning and use OpenAICompatibleProvider or Mock fallback
        try:
            return OpenAICompatibleProvider(api_key=api_key, base_url=base_url)
        except Exception as e:
            logger.warning(f"Failed to initialize '{provider_type}' provider: {e}. Falling back to MockAIProvider.")
            return MockAIProvider()

    # Default to MockAIProvider
    return MockAIProvider()
