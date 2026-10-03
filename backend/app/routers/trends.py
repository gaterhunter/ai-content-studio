from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..config import get_settings
from ..db import get_db
from ..models import Persona, TrendSnapshot
from ..services.trends import rank_trends
from .deps import get_persona, today

router = APIRouter(tags=["trend"])


@router.post("/trends", response_model=list[schemas.TrendOut], status_code=201)
def add_trends(body: list[schemas.TrendCreate], db: Session = Depends(get_db)):
    """MVP: nhập trend thủ công (từ quan sát, Google Trends, Creative Center...). V1 sẽ tự thu thập."""
    rows = [TrendSnapshot(**{**t.model_dump(), "observed_on": t.observed_on or today()}) for t in body]
    db.add_all(rows)
    db.commit()
    return rows


@router.get("/trends", response_model=list[schemas.TrendOut])
def list_trends(country: str = "VN", days: int = 14, db: Session = Depends(get_db)):
    since = today() - timedelta(days=days)
    return db.scalars(select(TrendSnapshot).where(
        TrendSnapshot.country == country, TrendSnapshot.observed_on >= since,
    ).order_by(TrendSnapshot.observed_on.desc())).all()


@router.get("/personas/{persona_id}/trends", response_model=list[schemas.RankedTrendOut])
def ranked_for_persona(p: Persona = Depends(get_persona), db: Session = Depends(get_db)):
    """Top 10 trend đã qua bộ lọc hợp persona và hợp thời điểm."""
    return [r.as_dict() for r in rank_trends(db, p, today(), get_settings().production_lead_days)]
