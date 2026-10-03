"""Module 1 – Persona: trích hồ sơ giọng từ bảng hỏi và bài cũ."""

from __future__ import annotations

from .. import prompts
from ..llm import LLMRequest, get_llm
from ..models import Persona


def extract_voice(persona: Persona) -> dict:
    ctx = {
        "name": persona.name, "niche": persona.niche, "goal": persona.revenue_goal.value,
        "questionnaire": persona.questionnaire or {}, "samples": persona.sample_posts or [],
    }
    result, _ = get_llm().generate_json(LLMRequest(
        task="persona_extract", tier="writer", system=prompts.BASE_SYSTEM,
        prompt=prompts.persona_extract_prompt(persona.name, persona.niche, persona.revenue_goal.value,
                                              ctx["questionnaire"], ctx["samples"]),
        schema=prompts.PERSONA_SCHEMA, context=ctx,
    ))
    return result
