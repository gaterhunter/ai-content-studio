"""Mô hình dữ liệu lõi (mục 5 của kế hoạch).

Một User có nhiều Persona/Channel. Persona là tài sản trung tâm: hồ sơ giọng
được chèn vào mọi bước sinh nội dung.
"""

from __future__ import annotations

import enum
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RevenueGoal(str, enum.Enum):
    ads = "ads"  # quảng cáo nền tảng
    affiliate = "affiliate"  # affiliate, TikTok Shop, Shopee Affiliate
    course = "course"  # bán khóa học / sản phẩm số / tư vấn
    brand_deal = "brand_deal"


class Platform(str, enum.Enum):
    tiktok = "tiktok"
    reels = "reels"
    shorts = "shorts"
    facebook = "facebook"


class FunnelStage(str, enum.Enum):
    attract = "attract"  # thu hút
    trust = "trust"  # tin tưởng
    sell = "sell"  # bán


class IdeaStatus(str, enum.Enum):
    proposed = "proposed"
    selected = "selected"
    dropped = "dropped"


class ReviewStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    rejected = "rejected"


class PublishStatus(str, enum.Enum):
    scheduled = "scheduled"
    posted = "posted"
    skipped = "skipped"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    personas: Mapped[list[Persona]] = relationship(back_populates="user", cascade="all, delete-orphan")
    channels: Mapped[list[Channel]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    platform: Mapped[Platform] = mapped_column(Enum(Platform))
    handle: Mapped[str] = mapped_column(String(255), default="")
    followers: Mapped[int] = mapped_column(Integer, default=0)
    # Token OAuth đã mã hóa (Fernet). MVP đăng thủ công nên thường để trống.
    encrypted_token: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="channels")


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    niche: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(8), default="VN")
    revenue_goal: Mapped[RevenueGoal] = mapped_column(Enum(RevenueGoal))
    platforms: Mapped[list[str]] = mapped_column(JSON, default=list)
    # Câu trả lời bảng hỏi 10 phút + 3–5 bài cũ
    questionnaire: Mapped[dict] = mapped_column(JSON, default=dict)
    sample_posts: Mapped[list[str]] = mapped_column(JSON, default=list)
    # Hồ sơ giọng có cấu trúc: tone, values, banned_topics, catchphrases,
    # differentiators, good_examples, bad_examples
    voice_profile: Mapped[dict] = mapped_column(JSON, default=dict)
    # Giờ đăng ưa thích do người dùng tự đặt, ghi đè gợi ý mặc định
    posting_times: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="personas")
    ideas: Mapped[list[Idea]] = relationship(back_populates="persona", cascade="all, delete-orphan")


class TrendSnapshot(Base):
    __tablename__ = "trend_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    observed_on: Mapped[date] = mapped_column(Date)
    platform: Mapped[Platform] = mapped_column(Enum(Platform))
    country: Mapped[str] = mapped_column(String(8), default="VN")
    kind: Mapped[str] = mapped_column(String(32), default="topic")  # sound | format | topic | keyword
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    popularity: Mapped[float] = mapped_column(Float, default=0.5)  # 0..1
    estimated_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="manual")


class Idea(Base):
    __tablename__ = "ideas"

    id: Mapped[int] = mapped_column(primary_key=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id", ondelete="CASCADE"))
    trend_id: Mapped[int | None] = mapped_column(ForeignKey("trend_snapshots.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    angle: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    funnel_stage: Mapped[FunnelStage] = mapped_column(Enum(FunnelStage))
    planned_for: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[IdeaStatus] = mapped_column(Enum(IdeaStatus), default=IdeaStatus.proposed)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    persona: Mapped[Persona] = relationship(back_populates="ideas")
    trend: Mapped[TrendSnapshot | None] = relationship()
    contents: Mapped[list[ContentPiece]] = relationship(back_populates="idea", cascade="all, delete-orphan")


class ContentPiece(Base):
    __tablename__ = "content_pieces"

    id: Mapped[int] = mapped_column(primary_key=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("ideas.id", ondelete="CASCADE"))
    platform: Mapped[Platform] = mapped_column(Enum(Platform))
    variant: Mapped[int] = mapped_column(Integer, default=1)
    hook: Mapped[str] = mapped_column(Text, default="")
    script: Mapped[list[dict]] = mapped_column(JSON, default=list)  # [{t, line, visual}]
    long_post: Mapped[str] = mapped_column(Text, default="")
    caption: Mapped[str] = mapped_column(Text, default="")
    hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)
    cta: Mapped[str] = mapped_column(Text, default="")
    voice_score: Mapped[float] = mapped_column(Float, default=0.0)
    compliance: Mapped[dict] = mapped_column(JSON, default=dict)
    review_status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.draft)
    edited: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    idea: Mapped[Idea] = relationship(back_populates="contents")
    publish_jobs: Mapped[list[PublishJob]] = relationship(back_populates="content", cascade="all, delete-orphan")


class Asset(Base):
    """File video/ảnh/âm thanh (dùng từ V1 khi có Video Studio)."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("content_pieces.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))  # video | image | audio
    uri: Mapped[str] = mapped_column(Text)


class PublishJob(Base):
    __tablename__ = "publish_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("content_pieces.id", ondelete="CASCADE"))
    platform: Mapped[Platform] = mapped_column(Enum(Platform))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[PublishStatus] = mapped_column(Enum(PublishStatus), default=PublishStatus.scheduled)
    post_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    content: Mapped[ContentPiece] = relationship(back_populates="publish_jobs")


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("content_pieces.id", ondelete="CASCADE"))
    day: Mapped[date] = mapped_column(Date)
    views: Mapped[int] = mapped_column(Integer, default=0)
    avg_watch_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)


class Revenue(Base):
    __tablename__ = "revenues"

    id: Mapped[int] = mapped_column(primary_key=True)
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id", ondelete="CASCADE"))
    content_id: Mapped[int | None] = mapped_column(ForeignKey("content_pieces.id", ondelete="SET NULL"), nullable=True)
    source: Mapped[RevenueGoal] = mapped_column(Enum(RevenueGoal))
    amount_vnd: Mapped[int] = mapped_column(Integer)
    day: Mapped[date] = mapped_column(Date)


class AppSetting(Base):
    """Cài đặt toàn ứng dụng (MVP chưa có đăng nhập nên dùng chung): nhà cung cấp AI và khóa API đã mã hóa."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
