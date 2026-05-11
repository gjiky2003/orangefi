"""Database connection, session management, and schema migration."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dependency for FastAPI routes to get a database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables and migrate schema if needed."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Migrate: add new auth columns added in security audit
        migrations = [
            # --- Borrower auth columns ---
            "ALTER TABLE borrowers ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(256)",
            "ALTER TABLE borrowers ADD COLUMN IF NOT EXISTS login_attempts INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE borrowers ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE NOT NULL",
            "ALTER TABLE borrowers ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ",
            "ALTER TABLE borrowers ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ",
            "ALTER TABLE borrowers ADD COLUMN IF NOT EXISTS last_login_ip VARCHAR(45)",
            "ALTER TABLE borrowers ADD COLUMN IF NOT EXISTS mfa_secret VARCHAR(64)",
            "ALTER TABLE borrowers ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE NOT NULL",
            # --- Admin auth columns ---
            "ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS login_attempts INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE NOT NULL",
            "ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ",
            "ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ",
            "ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS last_login_ip VARCHAR(45)",
        ]
        for sql in migrations:
            try:
                await conn.execute(text(sql))
            except Exception:
                pass  # Column may already exist
