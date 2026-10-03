from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..config import get_settings
from ..db import get_db
from ..models import Idea, Persona, Platform
from ..services import ideas as idea_service
from ..services import writer
from .deps import get_idea, get_persona, today

router = APIRouter(tags=["idea"])


@router.post("/personas/{persona_id}/ideas/generate", response_model=list[schemas.IdeaOut], status_code=201)
def generate(week_of: date | None = None, p: Persona = Depends(get_persona), db: Session = Depends(get_db)):
    day = week_of or today()
    start = idea_service.week_start(day)
    return idea_service.generate_week(db, p, start, get_settings().production_lead_days, today=today())


@router.get("/personas/{persona_id}/ideas", response_model=list[schemas.IdeaOut])
def list_ideas(p: Persona = Depends(get_persona), db: Session = Depends(get_db)):
    return db.scalars(select(Idea).where(Idea.persona_id == p.id).order_by(Idea.planned_for.desc(), Idea.id)).all()


@router.patch("/ideas/{idea_id}", response_model=schemas.IdeaOut)
def update_idea(body: schemas.IdeaUpdate, idea: Idea = Depends(get_idea), db: Session = Depends(get_db)):
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(idea, k, v)
    db.commit()
    return idea


@router.post("/ideas/{idea_id}/write", response_model=list[schemas.ContentOut], status_code=201)
def write(platform: Platform, variants: int = 2, idea: Idea = Depends(get_idea), db: Session = Depends(get_db)):
    return writer.write_for_idea(db, idea, platform, max(1, min(3, variants)))
