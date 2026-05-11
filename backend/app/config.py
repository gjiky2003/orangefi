# OrangeFi Backend Configuration
# All secrets loaded from environment variables

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── App ──
    APP_NAME: str = "OrangeFi"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production

    # ── Database ──
    DATABASE_URL: str = "postgresql+asyncpg://orangefi:orangefi@localhost:5432/orangefi"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://orangefi:orangefi@localhost:5432/orangefi"
    DB_ECHO: bool = False

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Auth ──
    SECRET_KEY: str  # MUST be set via environment — no default in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MFA_ISSUER_NAME: str = "OrangeFi"

    # ── Admin ──
    ADMIN_EMAIL: str = "admin@orangefi.com"
    ADMIN_PASSWORD: str  # MUST be set via environment — no default in production

    # ── Plaid ──
    PLAID_CLIENT_ID: Optional[str] = None
    PLAID_SECRET: Optional[str] = None
    PLAID_ENV: str = "sandbox"

    # ── Stripe ──
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None

    # ── Twilio ──
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None

    # ── SendGrid ──
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "noreply@orangefi.com"

    # ── DocuSign ──
    DOCUSIGN_ACCOUNT_ID: Optional[str] = None
    DOCUSIGN_CLIENT_ID: Optional[str] = None
    DOCUSIGN_CLIENT_SECRET: Optional[str] = None
    DOCUSIGN_AUTH_SERVER: str = "account-d.docusign.com"

    # ── S3/Object Storage ──
    S3_ENDPOINT: Optional[str] = None  # MinIO URL in dev
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: str = "orangefi-documents"
    S3_REGION: str = "us-east-1"

    # ── Credit Bureau (mock for MVP) ──
    CREDIT_BUREAU_API_KEY: Optional[str] = None
    CREDIT_BUREAU_BASE_URL: str = "https://api.mockbureau.com/v1"

    # ── Celery ──
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ── Rate Limiting ──
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_AUTH_PER_MINUTE: int = 5

    # ── Encryption ──
    ENCRYPTION_KEY: str  # 32-byte URL-safe base64 key for AES-256 Fernet — MUST be set

    # ── Model Paths ──
    MODEL_DIR: str = "./app/underwriting/models"

    # ── CORS ──
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000,https://orangefi-frontend.onrender.com,https://orangefi.com,https://www.orangefi.com"

    # ── Sentry ──
    SENTRY_DSN: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

    def model_post_init(self, __context) -> None:
        """Validate that required secrets are set in production."""
        import os
        if self.ENVIRONMENT == "production":
            errors = []
            if not self.SECRET_KEY or self.SECRET_KEY == "change-me-in-production-please-use-a-strong-key":
                errors.append("SECRET_KEY must be set to a strong random value in production")
            if not self.ADMIN_PASSWORD or self.ADMIN_PASSWORD == "Admin123!ChangeMe":
                errors.append("ADMIN_PASSWORD must be set to a strong password in production")
            if not self.ENCRYPTION_KEY:
                errors.append("ENCRYPTION_KEY must be set in production (generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')")
            if errors:
                import warnings
                for err in errors:
                    warnings.warn(f"Security Warning: {err}")


settings = Settings()
