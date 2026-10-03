"""Trend Radar (MVP: nhập trend thủ công, AI chấm độ hợp persona).

Hai bộ lọc trước khi thành ý tưởng:
1. Hợp persona: điểm fit đủ cao, không rủi ro cao.
2. Hợp thời điểm: còn đủ ngày để quay, duyệt và đăng; trend hết đà thì loại dù đang hot.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import prompts
from ..llm import LLMRequest, get_llm
from ..models import Persona, TrendSnapshot

# Vòng đời ước tính (ngày) khi chưa biết ngày hết hạn
DEFAULT_LIFETIME_DAYS = {"sound": 7, "format": 14, "topic": 10, "keyword": 5}
MIN_FIT = 0.5
TOP_N = 10


@dataclass
class RankedTrend:
    trend: TrendSnapshot
    fit: float
    risk: str
    note: str
    days_left: int
    timing: float
    score: float

    def as_dict(self) -> dict:
        t = self.trend
        return {
            "id": t.id, "title": t.title, "kind": t.kind, "platform": t.platform.value,
            "description": t.description, "popularity": t.popularity,
            "fit": self.fit, "risk": self.risk, "note": self.note,
            "days_left": self.days_left, "timing": self.timing, "score": self.score,
        }


def expiry_of(t: TrendSnapshot) -> date:
    return t.estimated_expiry or t.observed_on + timedelta(days=DEFAULT_LIFETIME_DAYS.get(t.kind, 7))


def timing_score(days_left: int, lead_days: int) -> float:
    if days_left < lead_days:
        return 0.0
    return round(min(1.0, days_left / 14), 2)


def candidate_trends(db: Session, persona: Persona, today: date, lead_days: int) -> list[TrendSnapshot]:
    platforms = persona.platforms or ["tiktok"]
    rows = db.scalars(
        select(TrendSnapshot).where(
            TrendSnapshot.country == persona.country,
            TrendSnapshot.platform.in_(platforms),
            TrendSnapshot.observed_on >= today - timedelta(days=30),
        )
    ).all()
    return [t for t in rows if (expiry_of(t) - today).days >= lead_days]


def rank_trends(db: Session, persona: Persona, today: date, lead_days: int) -> list[RankedTrend]:
    trends = candidate_trends(db, persona, today, lead_days)
    if not trends:
        return []
    payload = [{"id": t.id, "title": t.title, "kind": t.kind, "description": t.description} for t in trends]
    result, _ = get_llm().generate_json(LLMRequest(
        task="trend_fit", tier="fast", system=prompts.BASE_SYSTEM,
        prompt=prompts.trend_fit_prompt(persona, payload), schema=prompts.TREND_FIT_SCHEMA,
        context={"niche": persona.niche, "trends": payload},
    ))
    by_id = {s["trend_id"]: s for s in result["scores"]}
    ranked: list[RankedTrend] = []
    for t in trends:
        s = by_id.get(t.id)
        if not s:
            continue
        fit = max(0.0, min(1.0, float(s["fit"])))
        if fit < MIN_FIT or s["risk"] == "high":
            continue
        days_left = (expiry_of(t) - today).days
        timing = timing_score(days_left, lead_days)
        score = round(0.6 * fit + 0.25 * timing + 0.15 * t.popularity - (0.1 if s["risk"] == "medium" else 0), 3)
        ranked.append(RankedTrend(t, fit, s["risk"], s["note"], days_left, timing, score))
    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked[:TOP_N]
