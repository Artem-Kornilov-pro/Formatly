from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+asyncpg://formatly:formatly@localhost:5432/formatly"
    redis_url: str = "redis://localhost:6379/0"

    llm_provider: Literal["yandex", "anthropic"] = "yandex"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_model: str = "deepseek-v4-flash/latest"

    access_token_ttl_seconds: int = 15 * 60
    refresh_token_ttl_seconds: int = 30 * 24 * 60 * 60
    cors_origins: list[str] = ["http://localhost:5173"]
    uploads_dir: str = "/app/uploads"


@lru_cache
def get_settings() -> Settings:
    return Settings()
