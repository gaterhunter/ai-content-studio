from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..config import get_settings
from ..db import get_db
from ..models import ContentPiece, Idea, Persona, PublishJob, PublishStatus, ReviewStatus
from ..services import compliance, daily_pack, scheduler
from .deps import get_content, get_persona, today

router = APIRouter(tags=["content"])


@router.get("/personas/{persona_id}/daily-pack", response_model=schemas.DailyPackOut)
def get_daily_pack(day: date | None = None, p: Persona = Depends(get_persona), db: Session = Depends(get_db)):
    """Gói nội dung trong ngày: ý tưởng, 2 phương án cho mỗi nền tảng, giờ đăng gợi ý."""
    return daily_pack.build(db, p, day or today(), get_settings().production_lead_days)


@router.patch("/contents/{content_id}", response_model=schemas.ContentOut)
def edit_content(body: schemas.ContentEdit, c: ContentPiece = Depends(get_content), db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(c, k, v)
    if data:
        c.edited = True
        persona = c.idea.persona
        text = " ".join([c.hook, c.long_post, c.caption, " ".join(c.hashtags),
                         " ".join(s.get("line", "") for s in c.script)])
        notes = (c.compliance or {}).get("voice_notes", "")
        c.compliance = {**compliance.check(
            text, banned_topics=(persona.voice_profile or {}).get("banned_topics", []),
            disclosure_required=compliance.needs_disclosure(persona.revenue_goal.value, c.idea.funnel_stage.value),
        ), "voice_notes": notes}
    db.commit()
    return c


@router.post("/contents/{content_id}/approve", response_model=schemas.PublishJobOut)
def approve(body: schemas.ApproveIn | None = None, c: ContentPiece = Depends(get_content),
            db: Session = Depends(get_db)):
    """Duyệt một chạm: chốt phương án này, bỏ các phương án khác, đưa vào lịch đăng."""
    if not (c.compliance or {}).get("ok", True):
        raise HTTPException(422, "Nội dung còn lỗi tuân thủ mức cao, hãy sửa trước khi duyệt")
    c.review_status = ReviewStatus.approved
    c.approved_at = datetime.now(timezone.utc)
    for other in db.scalars(select(ContentPiece).where(
        ContentPiece.idea_id == c.idea_id, ContentPiece.platform == c.platform, ContentPiece.id != c.id,
    )):
        if other.review_status == ReviewStatus.draft:
            other.review_status = ReviewStatus.rejected
    when = (body.scheduled_at if body else None) or scheduler.suggest_slot(
        c.idea.persona, c.platform.value, c.idea.planned_for or today())
    job = db.scalar(select(PublishJob).where(PublishJob.content_id == c.id))
    if job:
        job.scheduled_at = when
    else:
        job = PublishJob(content_id=c.id, platform=c.platform, scheduled_at=when)
        db.add(job)
    db.commit()
    return job


@router.post("/contents/{content_id}/reject", response_model=schemas.ContentOut)
def reject(c: ContentPiece = Depends(get_content), db: Session = Depends(get_db)):
    c.review_status = ReviewStatus.rejected
    db.commit()
    return c


@router.get("/personas/{persona_id}/calendar", response_model=list[schemas.PublishJobOut])
def calendar(start: date | None = None, end: date | None = None, p: Persona = Depends(get_persona),
             db: Session = Depends(get_db)):
    q = (select(PublishJob).join(ContentPiece).join(Idea)
         .where(Idea.persona_id == p.id).order_by(PublishJob.scheduled_at))
    jobs = db.scalars(q).all()
    if start:
        jobs = [j for j in jobs if j.scheduled_at.date() >= start]
    if end:
        jobs = [j for j in jobs if j.scheduled_at.date() <= end]
    return jobs


@router.post("/publish-jobs/{job_id}/posted", response_model=schemas.PublishJobOut)
def mark_posted(job_id: int, body: schemas.MarkPostedIn, db: Session = Depends(get_db)):
    """MVP đăng thủ công: người dùng tự đăng rồi đánh dấu đã đăng (kèm link bài)."""
    job = db.get(PublishJob, job_id)
    if not job:
        raise HTTPException(404, "Không tìm thấy lịch đăng")
    job.status = PublishStatus.posted
    job.post_url = body.post_url
    job.posted_at = datetime.now(timezone.utc)
    db.commit()
    return job
