from datetime import date

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ContentPiece, Idea, Persona


def get_persona(persona_id: int, db: Session = Depends(get_db)) -> Persona:
    p = db.get(Persona, persona_id)
    if not p:
        raise HTTPException(404, "Không tìm thấy persona")
    return p


def get_idea(idea_id: int, db: Session = Depends(get_db)) -> Idea:
    i = db.get(Idea, idea_id)
    if not i:
        raise HTTPException(404, "Không tìm thấy ý tưởng")
    return i


def get_content(content_id: int, db: Session = Depends(get_db)) -> ContentPiece:
    c = db.get(ContentPiece, content_id)
    if not c:
        raise HTTPException(404, "Không tìm thấy nội dung")
    return c


def today() -> date:
    return date.today()
