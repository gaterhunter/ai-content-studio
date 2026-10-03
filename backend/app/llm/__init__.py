from functools import lru_cache

from ..config import get_settings
from .base import LLMClient, LLMError, LLMRequest, LLMUsage


@lru_cache
def get_llm() -> LLMClient:
    s = get_settings()
    if s.llm_provider == "anthropic":
        from .anthropic_client import AnthropicClient

        return AnthropicClient(s.anthropic_api_key, s.llm_writer_model, s.llm_fast_model, s.llm_use_fallbacks)
    from .mock_client import MockClient

    return MockClient()


__all__ = ["LLMClient", "LLMError", "LLMRequest", "LLMUsage", "get_llm"]
