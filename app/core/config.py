"""Strict Pydantic-Settings Environment Management Module

Defines strict type-validated configuration for the Save The Serve (S.T.S) platform.
"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = Field(default="Save The Serve (S.T.S) API", description="Application display name")
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="development, staging, or production")
    DEBUG: bool = Field(default=True, description="Enable debug diagnostics and SQL echo")
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"

    @property
    def cors_origins(self) -> List[str]:
        """Parsed list of allowed origins for CORS headers."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/save_the_serve",
        description="Async connection string using asyncpg driver",
    )
    DATABASE_URL_SYNC: Optional[str] = Field(
        default=None,
        description="Sync connection string for Alembic migrations using psycopg2",
    )
    SUPABASE_DB_POOL_URL: Optional[str] = Field(
        default=None,
        description="Transaction Pooler endpoint (PgBouncer port 6543) for serverless deployment",
    )
    DB_POOL_SIZE: int = Field(default=20, ge=1, le=100)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=5)
    DB_POOL_RECYCLE: int = Field(default=1800, ge=300)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_async_db_url(cls, v: Optional[str]) -> str:
        """Enforces postgresql+asyncpg:// scheme for native async driver compatibility."""
        if not v:
            return "postgresql+asyncpg://postgres:postgres@localhost:5432/save_the_serve"
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None

    JWT_SECRET_KEY: str = Field(
        default="sts_production_super_secret_signing_key_minimum_64_characters_long_12345",
        description="Cryptographic secret key for signing authentication tokens",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="Algorithm for JWT encryption")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, gt=0, description="Access token lifespan in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=14, gt=0, description="Refresh token lifespan in days")

    STORAGE_PROVIDER: str = "supabase"
    STORAGE_BUCKET_AVATARS: str = "sts-user-avatars"
    STORAGE_BUCKET_DONATIONS: str = "sts-donation-photos"
    STORAGE_BUCKET_DOCUMENTS: str = "sts-ngo-verification-docs"
    STORAGE_BUCKET_DELIVERY_PROOFS: str = "sts-delivery-proofs"

    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_CURRENCY: str = "usd"

    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None
    RAZORPAY_CURRENCY: str = "INR"

    POSTGIS_SRID: int = Field(default=4326, description="WGS84 EPSG:4326 standard coordinates")
    DEFAULT_SEARCH_RADIUS_KM: float = Field(default=25.0, gt=0)
    MAX_SEARCH_RADIUS_KM: float = Field(default=100.0, gt=0)

    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for real-time dispatch and queues",
    )


settings = Settings()
