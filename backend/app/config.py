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
    SECRET_KEY: str = ""  # Set via env SECRET_KEY or JWT_SECRET (fallback). MUST be strong in production
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
    ENCRYPTION_KEY: Optional[str] = None  # 32-byte URL-safe base64 key for AES-256 Fernet. Fallback to hex-32-byte for backward compat.

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
        """Backward-compat: fallback SECRET_KEY from JWT_SECRET env var."""
        import os
        # Backward compatibility: Render env has JWT_SECRET instead of SECRET_KEY
        if not self.SECRET_KEY:
            jwt_secret = os.environ.get("JWT_SECRET", "")
            if jwt_secret:
                object.__setattr__(self, "SECRET_KEY", jwt_secret)

        # Backward compatibility: ENCRYPTION_KEY may be hex-32 instead of base64
        if self.ENCRYPTION_KEY and len(self.ENCRYPTION_KEY) == 64:
            try:
                bytes.fromhex(self.ENCRYPTION_KEY)
                import base64
                object.__setattr__(self, "ENCRYPTION_KEY", base64.urlsafe_b64encode(bytes.fromhex(self.ENCRYPTION_KEY)).decode())
            except (ValueError, ImportError):
                pass

        if self.ENVIRONMENT == "production" or os.environ.get("SECRET_KEY_CHECK", "") == "1":
            warnings_list = []
            if len(self.SECRET_KEY) < 16:
                warnings_list.append("SECRET_KEY is too short or not set. Use: openssl rand -hex 32")
            try:
                from cryptography.fernet import Fernet
                if self.ENCRYPTION_KEY:
                    Fernet(self.ENCRYPTION_KEY.encode() if isinstance(self.ENCRYPTION_KEY, str) else self.ENCRYPTION_KEY)
            except Exception:
                pass  # Fernet will raise at point of use; acceptable fallback


settings = Settings()
