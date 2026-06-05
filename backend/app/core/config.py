from pydantic_settings import BaseSettings
from pydantic import AnyUrl, EmailStr
from functools import lru_cache
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "SiraFit API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: AnyUrl

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

    # Environment
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

settings = Settings()

