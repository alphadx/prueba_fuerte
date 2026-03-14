from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost/erp_db"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    APP_NAME: str = "ERP Barrio Chile"
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = ["*"]

    model_config = {"env_file": ".env"}


settings = Settings()

if not settings.DEBUG and settings.SECRET_KEY == "change-me-in-production":
    import warnings
    warnings.warn(
        "SECRET_KEY is set to the default placeholder value. "
        "Set a strong SECRET_KEY environment variable before deploying to production.",
        stacklevel=1,
    )
