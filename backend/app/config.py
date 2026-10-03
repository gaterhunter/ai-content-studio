from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./studio.db"
    llm_provider: str = "mock"  # "anthropic" | "mock"
    anthropic_api_key: str = ""
    llm_writer_model: str = "claude-opus-5-5"
    llm_fast_model: str = "claude-haiku-4-5"
    llm_use_fallbacks: bool = True
    token_encryption_key: str = ""
    production_lead_days: int = 2
    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
