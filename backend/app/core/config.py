from pydantic_settings import BaseSettings
from pydantic import EmailStr
from functools import lru_cache
import os
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "SiraFit API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database — plain str so both postgres:// and sqlite:// work
    DATABASE_URL: str

    # CORS
    CORS_ORIGINS: str

    # SMTP
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str
    SMTP_FROM: str = "noreply@sirafit.com"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery (optional)
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # Environment
    ENVIRONMENT: str = "development"

    # AI Integration
    GEMINI_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None

    # Data encryption for user-stored API keys (fall back to SECRET_KEY if not set)
    DATA_ENCRYPTION_KEY: str | None = None
    class Config:
        env_file = str(Path(__file__).resolve().parent.parent.parent.parent / ".env")
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

settings = Settings()
