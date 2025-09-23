from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings, loaded from environment variables or a .env file."""
    APP_NAME: str = "ClubConnect"
    ENV: str = "dev"

    DATABASE_URL: str = Field(...)
    SECRET_KEY: str = Field(...)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DEMO_API_KEY: str | None = None

    class Config:
        """Pydantic settings config."""
        env_file = ".env"
        case_sensitive = True


settings = Settings()
