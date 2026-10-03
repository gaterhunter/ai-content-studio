from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..db import get_db
from ..models import Persona, User
from ..services import persona as persona_service
from .deps import get_persona

router = APIRouter(tags=["persona"])


@router.post("/users", response_model=schemas.UserOut, status_code=201)
def create_user(body: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == body.email))
    if existing:
        return existing
    user = User(email=body.email, name=body.name)
    db.add(user)
    db.commit()
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Xoá toàn bộ dữ liệu của người dùng (persona, ý tưởng, nội dung, token, số liệu)."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Không tìm thấy người dùng")
    db.delete(user)
    db.commit()


@router.post("/personas", response_model=schemas.PersonaOut, status_code=201)
def create_persona(body: schemas.PersonaCreate, db: Session = Depends(get_db)):
    if not db.get(User, body.user_id):
        raise HTTPException(404, "Không tìm thấy người dùng")
    p = Persona(
        user_id=body.user_id, name=body.name, niche=body.niche, country=body.country,
        revenue_goal=body.revenue_goal, platforms=[pl.value for pl in body.platforms],
        questionnaire=body.questionnaire.model_dump(), sample_posts=body.sample_posts,
    )
    db.add(p)
    db.flush()
    p.voice_profile = persona_service.extract_voice(p)
    db.commit()
    return p


@router.get("/personas", response_model=list[schemas.PersonaOut])
def list_personas(user_id: int, db: Session = Depends(get_db)):
    return db.scalars(select(Persona).where(Persona.user_id == user_id).order_by(Persona.id)).all()


@router.get("/personas/{persona_id}", response_model=schemas.PersonaOut)
def read_persona(p: Persona = Depends(get_persona)):
    return p


@router.patch("/personas/{persona_id}", response_model=schemas.PersonaOut)
def update_persona(body: schemas.PersonaUpdate, p: Persona = Depends(get_persona), db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True)
    if "platforms" in data:
        data["platforms"] = [pl.value for pl in body.platforms or []]
    for k, v in data.items():
        setattr(p, k, v)
    db.commit()
    return p


@router.post("/personas/{persona_id}/re-extract", response_model=schemas.PersonaOut)
def re_extract(p: Persona = Depends(get_persona), db: Session = Depends(get_db)):
    p.voice_profile = persona_service.extract_voice(p)
    db.commit()
    return p
