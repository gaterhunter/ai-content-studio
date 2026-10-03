from __future__ import annotations

import json
import logging

import anthropic

from .base import LLMError, LLMRequest, LLMUsage

log = logging.getLogger(__name__)


class AnthropicClient:
    name = "anthropic"

    def __init__(self, api_key: str, writer_model: str, fast_model: str, use_fallbacks: bool = True):
        self._client = anthropic.Anthropic(api_key=api_key or None)
        self._models = {"writer": writer_model, "fast": fast_model}
        self._use_fallbacks = use_fallbacks

    def generate_json(self, req: LLMRequest) -> tuple[dict, LLMUsage]:
        model = self._models[req.tier]
        kwargs: dict = {
            "model": model,
            "max_tokens": 16000,
            "system": req.system,
            "messages": [{"role": "user", "content": req.prompt}],
            "output_config": {
                "effort": "medium" if req.tier == "writer" else "low",
                "format": {"type": "json_schema", "schema": req.schema},
            },
        }
        # Fallback phía server khi mô hình viết từ chối (chỉ áp dụng cho Opus 5.5).
        if self._use_fallbacks and model.startswith("claude-opus-5"):
            kwargs["betas"] = ["server-side-fallback-2026-07-01"]
            kwargs["fallbacks"] = "default"
        try:
            response = self._client.beta.messages.create(**kwargs)
        except anthropic.RateLimitError as e:
            raise LLMError("Bị giới hạn tốc độ gọi AI, thử lại sau") from e
        except anthropic.APIStatusError as e:
            raise LLMError(f"Lỗi API ({e.status_code}): {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise LLMError("Không kết nối được tới API") from e

        if response.stop_reason == "refusal":
            raise LLMError("Mô hình từ chối yêu cầu này")
        if response.stop_reason == "max_tokens":
            raise LLMError("Đầu ra bị cắt do vượt max_tokens")
        text = next((b.text for b in response.content if b.type == "text"), None)
        if text is None:
            raise LLMError("Không có nội dung trả về")
        usage = LLMUsage(model=response.model, input_tokens=response.usage.input_tokens,
                         output_tokens=response.usage.output_tokens)
        log.info("llm task=%s model=%s in=%s out=%s", req.task, usage.model, usage.input_tokens, usage.output_tokens)
        return json.loads(text), usage
