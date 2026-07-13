import json
from typing import Annotated, Any

from pydantic import BeforeValidator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
                return [str(parsed)]
            except Exception:
                return [v]
        return [str(x) for x in v]
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    PROJECT_NAME: str = "University Portal Backend"
    ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    BACKEND_CORS_ORIGINS: Annotated[list[str], BeforeValidator(parse_cors)] = []
    ALLOWED_HOSTS: Annotated[list[str], BeforeValidator(parse_cors)] = ["*"]
    
    # Security Configuration
    MAX_CONTENT_LENGTH: int = 10 * 1024 * 1024  # 10MB limit
    RATE_LIMIT_GLOBAL: str = "100/minute"
    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_AI: str = "10/minute"

    # Postgres
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres_password"
    POSTGRES_DB: str = "university_cms"

    SQLALCHEMY_DATABASE_URI: str = ""

    @model_validator(mode="after")
    def assemble_db_connection(self) -> "Settings":
        if not self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    REDIS_URL: str = ""

    @model_validator(mode="after")
    def assemble_redis_connection(self) -> "Settings":
        if not self.REDIS_URL:
            auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
            self.REDIS_URL = (
                f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            )
        return self

    # JWT Security
    SECRET_KEY: str = (
        "super-secret-key-change-in-production-super-secret-key-change-in-production"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520
    REFRESH_TOKEN_EXPIRE_DAYS: int = 8

    # Cookie Settings
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    LOG_FILE_PATH: str = "logs/app.log"

    # MinIO / S3 Storage Config
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_INTERNAL_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = "minio_admin"
    MINIO_SECRET_KEY: str = "minio_password"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "university-media"

    @model_validator(mode="after")
    def assemble_minio_internal_endpoint(self) -> "Settings":
        if not self.MINIO_INTERNAL_ENDPOINT:
            self.MINIO_INTERNAL_ENDPOINT = self.MINIO_ENDPOINT
        return self

    # AI Integration
    GEMINI_API_KEY: str = ""
    AI_PROVIDER: str = "omniroute"
    AI_BASE_URL: str = "http://localhost:8090"
    AI_API_KEY: str = "sk-omniroute-secret-key"
    AI_DEFAULT_MODEL: str = "gemini-2.5-flash"
    AI_EMBEDDING_MODEL: str = "embedding-model"

    # Translation Config (NLLB-200)
    TRANSLATION_MODEL_NAME: str = "facebook/nllb-200-distilled-1.3B"
    TRANSLATION_DEVICE: str = "auto"
    TRANSLATION_CACHE_TTL: int = 86400
    TRANSLATION_MAX_INPUT_LENGTH: int = 1000
    TRANSLATION_MAX_BATCH_SIZE: int = 50

    # VAPID Configurations for Web Push
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_CLAIM_EMAIL: str = "admin@itup.io.vn"



settings = Settings()


def resolve_html_urls(html_content: Any) -> Any:
    if not html_content or not isinstance(html_content, str):
        return html_content
    protocol = "https" if settings.MINIO_SECURE else "http"
    base_url = f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/"
    return html_content.replace('/api/v1/portal/media/file/', base_url)

