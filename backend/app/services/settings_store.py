"""Đọc/ghi cài đặt AI. Khóa lưu trong DB (mã hóa) được ưu tiên hơn biến môi trường."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..config import get_settings
from ..crypto import decrypt, encrypt
from ..models import AppSetting

PROVIDERS = ("mock", "gemini", "anthropic")
KEY_PROVIDERS = ("gemini", "anthropic")
PROVIDER_KEY = "llm_provider"


def _key_name(provider: str) -> str:
    return f"api_key:{provider}"


@dataclass
class LLMConfig:
    provider: str
    api_key: str


def _env_key(provider: str) -> str:
    s = get_settings()
    return {"gemini": s.gemini_api_key, "anthropic": s.anthropic_api_key}.get(provider, "")


def active_provider(db: Session) -> str:
    row = db.get(AppSetting, PROVIDER_KEY)
    return row.value if row and row.value in PROVIDERS else get_settings().llm_provider


def stored_key(db: Session, provider: str) -> str:
    row = db.get(AppSetting, _key_name(provider))
    return decrypt(row.value) if row else ""


def resolve(db: Session) -> LLMConfig:
    provider = active_provider(db)
    if provider == "mock":
        return LLMConfig("mock", "")
    return LLMConfig(provider, stored_key(db, provider) or _env_key(provider))


def save_key(db: Session, provider: str, api_key: str) -> None:
    db.merge(AppSetting(key=_key_name(provider), value=encrypt(api_key.strip())))
    db.commit()


def delete_key(db: Session, provider: str) -> None:
    row = db.get(AppSetting, _key_name(provider))
    if row:
        db.delete(row)
        db.commit()


def set_provider(db: Session, provider: str) -> None:
    db.merge(AppSetting(key=PROVIDER_KEY, value=provider))
    db.commit()


def mask(key: str) -> str:
    return f"••••{key[-4:]}" if len(key) >= 8 else "••••"


def status(db: Session) -> dict:
    s = get_settings()
    providers = {}
    for p in KEY_PROVIDERS:
        try:
            stored = stored_key(db, p)
            error = None
        except Exception as e:  # khóa mã hóa hỏng: báo thay vì làm sập trang
            stored, error = "", str(e)
        env = _env_key(p)
        providers[p] = {
            "configured": bool(stored or env),
            "source": "settings" if stored else ("env" if env else None),
            "masked": mask(stored or env) if (stored or env) else None,
            "error": error,
            "writer_model": s.llm_gemini_writer_model if p == "gemini" else s.llm_writer_model,
            "fast_model": s.llm_gemini_fast_model if p == "gemini" else s.llm_fast_model,
        }
    return {"provider": active_provider(db), "providers": providers,
            "can_store_keys": bool(s.token_encryption_key)}
