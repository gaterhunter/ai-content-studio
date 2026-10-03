from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..db import get_db
from ..models import ContentPiece, Metric, Persona, Revenue
from ..services import analytics
from .deps import get_persona

router = APIRouter(tags=["analytics"])


@router.post("/metrics", status_code=201)
def add_metric(body: schemas.MetricIn, db: Session = Depends(get_db)):
    if not db.get(ContentPiece, body.content_id):
        raise HTTPException(404, "Không tìm thấy nội dung")
    db.add(Metric(**body.model_dump()))
    db.commit()
    return {"ok": True}


@router.post("/revenues", status_code=201)
def add_revenue(body: schemas.RevenueIn, db: Session = Depends(get_db)):
    if not db.get(Persona, body.persona_id):
        raise HTTPException(404, "Không tìm thấy persona")
    db.add(Revenue(**body.model_dump()))
    db.commit()
    return {"ok": True}


@router.get("/personas/{persona_id}/report")
def report(p: Persona = Depends(get_persona), db: Session = Depends(get_db)):
    return {"content": analytics.content_stats(db, p), "learnings": analytics.learnings(db, p)}
