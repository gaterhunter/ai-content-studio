from __future__ import annotations

from ..config import get_settings
from .base import LLMClient, LLMError, LLMRequest, LLMUsage


def build_client(provider: str, api_key: str) -> LLMClient:
    s = get_settings()
    if provider == "anthropic":
        if not api_key:
            raise LLMError("Chưa có API key Claude. Vào Cài đặt để thêm.")
        from .anthropic_client import AnthropicClient

        return AnthropicClient(api_key, s.llm_writer_model, s.llm_fast_model, s.llm_use_fallbacks)
    if provider == "gemini":
        from .gemini_client import GeminiClient

        return GeminiClient(api_key, s.llm_gemini_writer_model, s.llm_gemini_fast_model)
    from .mock_client import MockClient

    return MockClient()


def get_llm() -> LLMClient:
    """Chọn nhà cung cấp theo Cài đặt trong DB (rồi tới biến môi trường) mỗi lần gọi."""
    from ..crypto import CryptoError
    from ..db import SessionLocal
    from ..services import settings_store

    with SessionLocal() as db:
        try:
            cfg = settings_store.resolve(db)
        except CryptoError as e:
            raise LLMError(str(e)) from e
    return build_client(cfg.provider, cfg.api_key)


__all__ = ["LLMClient", "LLMError", "LLMRequest", "LLMUsage", "build_client", "get_llm"]
