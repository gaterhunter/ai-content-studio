from __future__ import annotations

import json
import logging

from google import genai
from google.genai import errors, types

from .base import LLMError, LLMRequest, LLMUsage

log = logging.getLogger(__name__)


class GeminiClient:
    name = "gemini"

    def __init__(self, api_key: str, writer_model: str, fast_model: str):
        if not api_key:
            raise LLMError("Chưa có API key Gemini. Vào Cài đặt để thêm.")
        self._client = genai.Client(api_key=api_key)
        self._models = {"writer": writer_model, "fast": fast_model}

    def generate_json(self, req: LLMRequest) -> tuple[dict, LLMUsage]:
        model = self._models[req.tier]
        try:
            response = self._client.models.generate_content(
                model=model,
                contents=req.prompt,
                config=types.GenerateContentConfig(
                    system_instruction=req.system,
                    response_mime_type="application/json",
                    response_json_schema=req.schema,
                ),
            )
        except errors.APIError as e:
            if e.code == 429:
                raise LLMError("Gemini đang giới hạn tốc độ hoặc hết hạn mức, thử lại sau") from e
            if e.code in (400, 401, 403) and "api key" in (e.message or "").lower():
                raise LLMError("API key Gemini không hợp lệ, hãy kiểm tra lại trong Cài đặt") from e
            raise LLMError(f"Lỗi Gemini ({e.code}): {e.message}") from e
        except Exception as e:  # lỗi mạng
            raise LLMError("Không kết nối được tới Gemini") from e

        text = response.text
        if not text:
            reason = response.prompt_feedback.block_reason if response.prompt_feedback else None
            raise LLMError(f"Gemini không trả nội dung{f' (bị chặn: {reason})' if reason else ''}")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise LLMError("Gemini trả về JSON không hợp lệ, thử lại") from e
        u = response.usage_metadata
        usage = LLMUsage(model=model, input_tokens=(u.prompt_token_count or 0) if u else 0,
                         output_tokens=(u.candidates_token_count or 0) if u else 0)
        log.info("llm task=%s model=%s in=%s out=%s", req.task, model, usage.input_tokens, usage.output_tokens)
        return data, usage
