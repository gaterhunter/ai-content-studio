"""Lớp trung gian gọi mô hình AI, để đổi nhà cung cấp khi giá/chất lượng thay đổi."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

Tier = Literal["writer", "fast"]


@dataclass
class LLMRequest:
    task: str  # tên tác vụ: persona_extract | trend_fit | ideas | write_content
    system: str
    prompt: str
    schema: dict  # JSON schema của đầu ra
    tier: Tier = "writer"
    # Dữ liệu có cấu trúc của đầu vào; mock dùng để sinh kết quả không cần mạng
    context: dict = field(default_factory=dict)


@dataclass
class LLMUsage:
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


class LLMError(RuntimeError):
    pass


class LLMClient(Protocol):
    name: str

    def generate_json(self, req: LLMRequest) -> tuple[dict, LLMUsage]: ...
