"""Module 4 – Viết nội dung: 2–3 phương án cho mỗi nền tảng, tự chấm giọng, kiểm tra tuân thủ."""

from __future__ import annotations

from sqlalchemy.orm import Session

from .. import prompts
from ..llm import LLMRequest, get_llm
from ..models import ContentPiece, Idea, Platform
from . import compliance


def write_for_idea(db: Session, idea: Idea, platform: Platform, n_variants: int = 2) -> list[ContentPiece]:
    persona = idea.persona
    disclosure = compliance.needs_disclosure(persona.revenue_goal.value, idea.funnel_stage.value)
    idea_payload = {"title": idea.title, "angle": idea.angle, "reason": idea.reason,
                    "funnel_stage": idea.funnel_stage.value,
                    "trend": idea.trend.title if idea.trend else None}
    result, _ = get_llm().generate_json(LLMRequest(
        task="write_content", tier="writer", system=prompts.BASE_SYSTEM,
        prompt=prompts.content_prompt(persona, idea_payload, platform.value, n_variants, disclosure),
        schema=prompts.CONTENT_SCHEMA,
        context={"idea": idea_payload, "niche": persona.niche, "n_variants": n_variants,
                 "needs_disclosure": disclosure},
    ))
    banned = (persona.voice_profile or {}).get("banned_topics", [])
    pieces: list[ContentPiece] = []
    for i, v in enumerate(result["variants"][:n_variants], start=1):
        full_text = " ".join([v["hook"], v["long_post"], v["caption"], " ".join(v["hashtags"]),
                              " ".join(s["line"] for s in v["script"])])
        pieces.append(ContentPiece(
            idea_id=idea.id, platform=platform, variant=i,
            hook=v["hook"], script=v["script"], long_post=v["long_post"], caption=v["caption"],
            hashtags=v["hashtags"], cta=v["cta"],
            voice_score=max(0.0, min(1.0, float(v["voice_score"]))),
            compliance={**compliance.check(full_text, banned_topics=banned, disclosure_required=disclosure),
                        "voice_notes": v["voice_notes"]},
        ))
    db.add_all(pieces)
    db.commit()
    return pieces
