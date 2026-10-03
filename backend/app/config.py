import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./studio.db"
    llm_provider: str = "mock"  # "anthropic" | "gemini" | "mock"
    anthropic_api_key: str = ""
    llm_writer_model: str = "claude-opus-5-5"
    llm_fast_model: str = "claude-haiku-4-5"
    gemini_api_key: str = ""
    llm_gemini_writer_model: str = "gemini-2.5-pro"
    llm_gemini_fast_model: str = "gemini-2.5-flash"
    llm_use_fallbacks: bool = True
    token_encryption_key: str = ""
    production_lead_days: int = 2
    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    # Vercel chỉ ghi được vào /tmp và dữ liệu mất khi instance tái tạo: chỉ để chạy thử,
    # dùng DATABASE_URL trỏ tới Postgres cho dữ liệu thật.
    if os.environ.get("VERCEL") and s.database_url.startswith("sqlite:///./"):
        s.database_url = "sqlite:////tmp/studio.db"
    return s
