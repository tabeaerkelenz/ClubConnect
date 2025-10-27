# app/core/config.py
from __future__ import annotations
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # App
    APP_NAME: str = "ClubConnect"
    ENV: str = "dev"  # dev | test | prod

    # DB (universal; works for Postgres or SQLite)
    DATABASE_URL: str = Field(default="sqlite+pysqlite:///:memory:")

    # Auth
    SECRET_KEY: str = "test-secret"          # override in prod
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Optional extras
    DEMO_API_KEY: str | None = None

    # pydantic-settings v2 config
    model_config = SettingsConfigDict(
        env_file=".env",             # default; can be overridden at init
        env_file_encoding="utf-8",
        extra="ignore",              # ignore unknown vars instead of raising
        case_sensitive=True,
    )

def load_settings() -> Settings:
    """
    Choose env file dynamically:
      - APP_ENV=test -> .env.test
      - otherwise    -> .env
    Values from real env vars always win over files.
    """
    app_env = os.getenv("APP_ENV", "dev").lower()
    env_file = ".env.test" if app_env == "test" else ".env"
    return Settings(_env_file=env_file)

# Singleton used by the app. Tests can still override behavior with APP_ENV/env vars.
settings = load_settings()
