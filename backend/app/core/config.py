from pydantic_settings import BaseSettings
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
    REDIS_URL: str = "redis://localhost:6381/0"

    # Frontend URL (used for verification/reset links in emails)
    FRONTEND_URL: str = "http://localhost:8080"

    # Celery (optional)
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # Environment & Release
    ENVIRONMENT: str = "development"
    RELEASE_VERSION: str = "1.0.0"

    # Observability & Tracing (Sprint 15)
    ENABLE_TRACING: bool = False
    OTLP_ENDPOINT: str | None = None
    OTLP_INSECURE: bool = True
    OTEL_SAMPLE_RATE: float = 1.0

    # Centralized Error Tracking (Sprint 15)
    ERROR_TRACKING_DSN: str | None = None
    ERROR_TRACKING_ENABLED: bool = False
    ERROR_TRACKING_SAMPLE_RATE: float = 1.0

    # Metrics & Backups (Sprint 15)
    METRICS_ENABLED: bool = True
    BACKUP_ENABLED: bool = True
    BACKUP_DIR: str = "/var/backups/sirafit"
    BACKUP_RETENTION_DAYS: int = 14
    BACKUP_REMOTE_TARGET: str | None = None
    BACKUP_ENCRYPTION_KEY: str | None = None

    # Semantic Search & Embeddings (Sprint 8)
    ENABLE_EMBEDDINGS: bool = True
    ENABLE_SEMANTIC_SEARCH: bool = True
    DEFAULT_SEARCH_MODE: str = "keyword"  # keyword | semantic | hybrid
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_VERSION: str = "v1"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_NORMALIZE: bool = True
    EMBEDDING_MAX_INPUT_TOKENS: int = 256
    EMBEDDING_BATCH_SIZE: int = 32

    # AI Integration — one field per supported provider. All optional; the
    # agent connection check and generation dispatcher pick the first key set.
    GEMINI_API: str | None = None
    GEMINI_API_KEY: str | None = None
    OPENROUTER_API: str | None = None
    OPENROUTER_API_KEY: str | None = None
    ANTHROPIC_API: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API: str | None = None
    OPENAI_API_KEY: str | None = None
    GROK_API: str | None = None
    GROK_API_KEY: str | None = None
    XAI_API_KEY: str | None = None
    MISTRAL_API: str | None = None
    MISTRAL_API_KEY: str | None = None
    NVIDIA_API: str | None = None
    NVIDIA_API_KEY: str | None = None

    # Data encryption for user-stored API keys (fall back to SECRET_KEY if not set)
    DATA_ENCRYPTION_KEY: str | None = None

    # OAuth / Social Login
    ENABLE_OAUTH: bool = True
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None
    GITHUB_REDIRECT_URI: str | None = None
    LINKEDIN_CLIENT_ID: str | None = None
    LINKEDIN_CLIENT_SECRET: str | None = None
    LINKEDIN_REDIRECT_URI: str | None = None

    # 2FA / TOTP
    ENABLE_2FA: bool = True
    TOTP_ISSUER_NAME: str = "SiraFit"
    RECOVERY_CODE_COUNT: int = 8

    # Analytics Expansion (Sprint 10)
    SALARY_BENCHMARK_MIN_SAMPLES: int = 5
    SALARY_BENCHMARK_MAX_ROLES: int = 10
    SKILLS_GAP_TOP_N: int = 15
    SKILLS_GAP_PRIORITY_THRESHOLD: float = 0.20
    SKILLS_GAP_HIGH_MATCH_THRESHOLD: float = 0.70
    STAGE_MEDIAN_MIN_APPLICATIONS: int = 3

    # Optional path to a user-supplied .env file holding provider API keys.
    # When set, keys in this file OVERLAY the server .env fields (see
    # app.services.ai_keys.get_env_provider_keys). This lets a self-hoster drop
    # their own keys file in instead of pasting them into the Settings UI.
    USER_KEYS_ENV_FILE: str | None = None

    # Provider-to-API-key mapping: maps AI provider names to their corresponding
    # settings field names. Used by job_analysis.py, resume_generation.py, and
    # cover_letter_generation.py to resolve which API key to use.
    # Extracting this here avoids duplication across 3 service files.
    PROVIDER_KEY_FIELDS: dict[str, str] = {
        "gemini": "GEMINI_API",
        "openrouter": "OPENROUTER_API",
        "anthropic": "ANTHROPIC_API",
        "openai": "OPENAI_API",
        "grok": "GROK_API",
        "mistral": "MISTRAL_API",
        "nvidia": "NVIDIA_API",
    }

    class Config:
        _root_env = Path(__file__).resolve().parent.parent.parent.parent / ".env"
        _backend_env = Path(__file__).resolve().parent.parent.parent / ".env"
        env_file = [str(_root_env), str(_backend_env)]
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
