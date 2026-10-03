from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import FunnelStage, IdeaStatus, Platform, PublishStatus, ReviewStatus, RevenueGoal


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: str
    name: str = ""


class UserOut(ORM):
    id: int
    email: str
    name: str


class Questionnaire(BaseModel):
    """Bảng hỏi 10 phút. Mọi trường đều tùy chọn để người dùng bắt đầu nhanh."""

    about_me: str = ""
    audience: str = ""
    tone: str = ""
    values: list[str] = []
    banned_topics: list[str] = []
    catchphrases: list[str] = []
    differentiators: list[str] = []
    comfortable_on_camera: bool | None = None
    hours_per_week: int | None = None
    products_or_offers: str = ""


class PersonaCreate(BaseModel):
    user_id: int
    name: str
    niche: str
    country: str = "VN"
    revenue_goal: RevenueGoal
    platforms: list[Platform] = [Platform.tiktok, Platform.reels]
    questionnaire: Questionnaire = Questionnaire()
    sample_posts: list[str] = Field(default_factory=list, max_length=10)


class PersonaUpdate(BaseModel):
    niche: str | None = None
    revenue_goal: RevenueGoal | None = None
    platforms: list[Platform] | None = None
    voice_profile: dict | None = None
    posting_times: dict[str, list[str]] | None = None


class PersonaOut(ORM):
    id: int
    user_id: int
    name: str
    niche: str
    country: str
    revenue_goal: RevenueGoal
    platforms: list[str]
    questionnaire: dict
    sample_posts: list[str]
    voice_profile: dict
    posting_times: dict


class TrendCreate(BaseModel):
    platform: Platform
    title: str
    kind: str = Field("topic", pattern="^(sound|format|topic|keyword)$")
    description: str = ""
    country: str = "VN"
    popularity: float = Field(0.5, ge=0, le=1)
    observed_on: date | None = None
    estimated_expiry: date | None = None
    source: str = "manual"


class TrendOut(ORM):
    id: int
    platform: Platform
    title: str
    kind: str
    description: str
    country: str
    popularity: float
    observed_on: date
    estimated_expiry: date | None


class RankedTrendOut(BaseModel):
    id: int
    title: str
    kind: str
    platform: str
    description: str
    popularity: float
    fit: float
    risk: str
    note: str
    days_left: int
    timing: float
    score: float


class IdeaOut(ORM):
    id: int
    persona_id: int
    trend_id: int | None
    title: str
    angle: str
    reason: str
    funnel_stage: FunnelStage
    planned_for: date | None
    status: IdeaStatus


class IdeaUpdate(BaseModel):
    status: IdeaStatus | None = None
    planned_for: date | None = None
    title: str | None = None
    angle: str | None = None


class ContentOut(ORM):
    id: int
    idea_id: int
    platform: Platform
    variant: int
    hook: str
    script: list[dict]
    long_post: str
    caption: str
    hashtags: list[str]
    cta: str
    voice_score: float
    compliance: dict
    review_status: ReviewStatus
    edited: bool
    approved_at: datetime | None


class ContentEdit(BaseModel):
    hook: str | None = None
    script: list[dict] | None = None
    long_post: str | None = None
    caption: str | None = None
    hashtags: list[str] | None = None
    cta: str | None = None


class ApproveIn(BaseModel):
    scheduled_at: datetime | None = None  # bỏ trống thì dùng giờ gợi ý


class PublishJobOut(ORM):
    id: int
    content_id: int
    platform: Platform
    scheduled_at: datetime
    status: PublishStatus
    post_url: str | None
    posted_at: datetime | None


class MarkPostedIn(BaseModel):
    post_url: str | None = None


class DailyItem(BaseModel):
    platform: str
    suggested_time: str
    drafts: list[ContentOut]


class DailyPackOut(BaseModel):
    date: str
    persona_id: int
    idea: IdeaOut | None
    items: list[DailyItem]


class MetricIn(BaseModel):
    content_id: int
    day: date
    views: int = 0
    avg_watch_ratio: float = Field(0, ge=0, le=1)
    saves: int = 0
    shares: int = 0
    conversions: int = 0


class RevenueIn(BaseModel):
    persona_id: int
    content_id: int | None = None
    source: RevenueGoal
    amount_vnd: int = Field(ge=0)
    day: date
