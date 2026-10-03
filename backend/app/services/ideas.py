"""Module 3 – Idea Engine: 7 ý tưởng/tuần, mỗi ý gắn một bước phễu."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import prompts
from ..llm import LLMRequest, get_llm
from ..models import FunnelStage, Idea, IdeaStatus, Persona
from . import analytics
from .trends import rank_trends

# Tỉ lệ thu hút / tin tưởng / bán theo mục tiêu kiếm tiền (7 bài/tuần)
STAGE_MIX = {
    "ads": {"attract": 4, "trust": 2, "sell": 1},
    "affiliate": {"attract": 3, "trust": 2, "sell": 2},
    "course": {"attract": 2, "trust": 3, "sell": 2},
    "brand_deal": {"attract": 3, "trust": 3, "sell": 1},
}


def stage_plan(goal: str, n: int = 7) -> list[str]:
    """Rải đều các bước phễu trong tuần thay vì dồn một chỗ."""
    base = STAGE_MIX.get(goal, STAGE_MIX["ads"])
    plan: list[str] = []
    remaining = dict(base)
    while len(plan) < n:
        if not any(remaining.values()):
            remaining = dict(base)  # n > 7 thì lặp lại tỉ lệ
        for stage in ("attract", "trust", "sell"):
            if remaining[stage] and len(plan) < n:
                plan.append(stage)
                remaining[stage] -= 1
    return plan


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def generate_week(db: Session, persona: Persona, start: date, lead_days: int, n: int = 7,
                  today: date | None = None) -> list[Idea]:
    # Độ trễ của trend tính theo hôm nay, không theo đầu tuần
    ranked = rank_trends(db, persona, max(start, today or start), lead_days)
    trends = [r.as_dict() for r in ranked]
    recent = db.scalars(
        select(Idea.title).where(Idea.persona_id == persona.id).order_by(Idea.created_at.desc()).limit(20)
    ).all()
    learnings = analytics.learnings(db, persona)
    plan = stage_plan(persona.revenue_goal.value, n)
    result, _ = get_llm().generate_json(LLMRequest(
        task="ideas", tier="writer", system=prompts.BASE_SYSTEM,
        prompt=prompts.ideas_prompt(persona, trends, plan, list(recent), learnings),
        schema=prompts.IDEAS_SCHEMA,
        context={"niche": persona.niche, "persona_name": persona.name, "goal": persona.revenue_goal.value,
                 "trends": trends, "stage_plan": plan},
    ))
    valid_trend_ids = {t["id"] for t in trends}
    ideas: list[Idea] = []
    for i, item in enumerate(result["ideas"][:n]):
        ideas.append(Idea(
            persona_id=persona.id,
            trend_id=item["trend_id"] if item["trend_id"] in valid_trend_ids else None,
            title=item["title"], angle=item["angle"], reason=item["reason"],
            funnel_stage=FunnelStage(item["funnel_stage"]),
            planned_for=start + timedelta(days=i),
            status=IdeaStatus.proposed,
        ))
    db.add_all(ideas)
    db.commit()
    return ideas
