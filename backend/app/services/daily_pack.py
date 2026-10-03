"""Gói nội dung mỗi ngày: ý tưởng + bản nháp cho từng nền tảng + giờ đăng gợi ý."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentPiece, Idea, IdeaStatus, Persona, Platform
from . import ideas as idea_service
from . import scheduler, writer


def ensure_week(db: Session, persona: Persona, day: date, lead_days: int) -> None:
    """Sinh 7 ý tưởng cho tuần chứa `day` nếu tuần đó chưa có."""
    start = idea_service.week_start(day)
    exists = db.scalar(select(Idea.id).where(
        Idea.persona_id == persona.id, Idea.planned_for >= start, Idea.planned_for < start + timedelta(days=7),
    ).limit(1))
    if exists is None:
        idea_service.generate_week(db, persona, start, lead_days, today=day)


def build(db: Session, persona: Persona, day: date, lead_days: int) -> dict:
    ensure_week(db, persona, day, lead_days)
    idea = db.scalar(select(Idea).where(
        Idea.persona_id == persona.id, Idea.planned_for == day, Idea.status != IdeaStatus.dropped,
    ).order_by(Idea.id))
    if idea is None:
        return {"date": day.isoformat(), "persona_id": persona.id, "idea": None, "items": []}
    if idea.status == IdeaStatus.proposed:
        idea.status = IdeaStatus.selected
        db.commit()

    items = []
    for platform_name in persona.platforms or ["tiktok"]:
        platform = Platform(platform_name)
        drafts = db.scalars(select(ContentPiece).where(
            ContentPiece.idea_id == idea.id, ContentPiece.platform == platform,
        ).order_by(ContentPiece.variant)).all()
        if not drafts:
            drafts = writer.write_for_idea(db, idea, platform)
        items.append({
            "platform": platform.value,
            "suggested_time": scheduler.suggest_slot(persona, platform.value, day).isoformat(),
            "drafts": drafts,
        })
    return {"date": day.isoformat(), "persona_id": persona.id, "idea": idea, "items": items}
