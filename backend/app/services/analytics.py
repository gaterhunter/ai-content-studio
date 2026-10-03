"""Module 7 (bản tối giản cho MVP): nhập số liệu thủ công, rút bài học cho Idea Engine."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import ContentPiece, Idea, Metric, Persona


def content_stats(db: Session, persona: Persona) -> list[dict]:
    rows = db.execute(
        select(Idea.title, Idea.funnel_stage, func.sum(Metric.views), func.avg(Metric.avg_watch_ratio),
               func.sum(Metric.saves), func.sum(Metric.shares), func.sum(Metric.conversions))
        .join(ContentPiece, ContentPiece.idea_id == Idea.id)
        .join(Metric, Metric.content_id == ContentPiece.id)
        .where(Idea.persona_id == persona.id)
        .group_by(Idea.id)
    ).all()
    stats = []
    for title, stage, views, watch, saves, shares, conv in rows:
        views = views or 0
        stats.append({
            "title": title, "funnel_stage": stage.value, "views": views,
            "avg_watch_ratio": round(watch or 0, 3),
            "save_share_rate": round(((saves or 0) + (shares or 0)) / views, 4) if views else 0.0,
            "conversions": conv or 0,
        })
    return stats


def learnings(db: Session, persona: Persona, top: int = 3) -> list[str]:
    stats = content_stats(db, persona)
    if not stats:
        return []
    out: list[str] = []
    for s in sorted(stats, key=lambda s: s["avg_watch_ratio"], reverse=True)[:top]:
        out.append(f"Giữ chân tốt ({s['avg_watch_ratio']:.0%}): «{s['title']}»")
    for s in sorted(stats, key=lambda s: s["conversions"], reverse=True)[:1]:
        if s["conversions"]:
            out.append(f"Ra chuyển đổi nhiều nhất ({s['conversions']}): «{s['title']}»")
    return out
