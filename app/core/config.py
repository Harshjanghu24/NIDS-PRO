import json
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # Environment
    ENVIRONMENT: str = Field(default="development", description="System execution environment")
    APP_NAME: str = Field(default="NIDS-Platform", description="Application name")
    APP_VERSION: str = Field(default="2.0.0-DRAFT", description="Application version")
    DEBUG: bool = Field(default=True, description="Debug mode flag")
    LOG_LEVEL: str = Field(default="INFO", description="Logging verbosity level")

    # Server Binding
    HOST: str = Field(default="0.0.0.0", description="Server host address")
    PORT: int = Field(default=8000, description="Server port")

    # Security
    SECRET_KEY: str = Field(
        default="change_this_to_a_secure_random_key_in_production_min32chars",
        description="Secret key for JWT token signatures"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token TTL in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token TTL in days")

    # Database Settings (PostgreSQL 15)
    POSTGRES_USER: str = Field(default="nids_user", description="Postgres database user")
    POSTGRES_PASSWORD: str = Field(default="nids_password", description="Postgres user password")
    POSTGRES_DB: str = Field(default="nids_db", description="Postgres database name")
    POSTGRES_HOST: str = Field(default="localhost", description="Postgres host")
    POSTGRES_PORT: int = Field(default=5432, description="Postgres port")
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://nids_user:nids_password@localhost:5432/nids_db",
        description="Async SQLAlchemy database connection URI"
    )

    # Redis Settings (Redis 7)
    REDIS_HOST: str = Field(default="localhost", description="Redis server host")
    REDIS_PORT: int = Field(default=6379, description="Redis server port")
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URI"
    )

    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173"
        ],
        description="Allowed CORS origin URLs"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Invalid LOG_LEVEL '{v}'. Must be one of {valid_levels}")
        return upper_v


settings = Settings()
