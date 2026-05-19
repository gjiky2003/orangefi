"""
OrangeFi Lending Platform — FastAPI Application Factory.

Creates and configures the ASGI application with middleware, exception
handlers, routers, startup logic, and monitoring endpoints.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import async_session_factory, init_db, engine
from app.models import AdminRole, AdminUser
from app.routers import admin_router, borrower_router, health_router, integrations_router, underwriting_router, servicing_router, compliance_router, agent_router
from app.utils.rate_limit import get_rate_limiter
from app.utils.security import hash_password

# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("orangefi")

# ──────────────────────────────────────────────────────────────────────────────
# Sentry (optional)
# ──────────────────────────────────────────────────────────────────────────────

_sentry_initialized = False


def _init_sentry() -> None:
    """Initialise Sentry SDK if a DSN is configured."""
    global _sentry_initialized
    if _sentry_initialized:
        return
    dsn = settings.SENTRY_DSN
    if not dsn:
        logger.info("Sentry DSN not set — error tracking disabled")
        return
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=dsn,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.2 if settings.ENVIRONMENT == "production" else 1.0,
            send_default_pii=False,
        )
        _sentry_initialized = True
        logger.info("Sentry initialised successfully")
    except Exception as exc:
        logger.warning("Failed to initialise Sentry: %s", exc)


# ──────────────────────────────────────────────────────────────────────────────
# Startup / Shutdown
# ──────────────────────────────────────────────────────────────────────────────

_start_time: float = 0.0


async def _create_admin_user() -> None:
    """Ensure the default admin user exists on startup."""
    from sqlalchemy import select

    async with async_session_factory() as session:
        result = await session.execute(
            select(AdminUser).where(AdminUser.email == settings.ADMIN_EMAIL)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            # Always update the password to match current env var
            new_hash = hash_password(settings.ADMIN_PASSWORD)
async def _create_admin_user() -> None:
    """Ensure the default admin user exists and password is current."""
    from sqlalchemy import select

    # Log the configured admin password (first 4 chars only for verification)
    pw = settings.ADMIN_PASSWORD or ""
    logger.info("ADMIN_PASSWORD from env: %s... (len=%d)", pw[:4], len(pw))

    async with async_session_factory() as session:
        result = await session.execute(
            select(AdminUser).where(AdminUser.email == settings.ADMIN_EMAIL)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            # Update password if the env var changed (e.g. after redeploy)
            new_hash = hash_password(settings.ADMIN_PASSWORD)
            if existing.hashed_password != new_hash or True:  # Always sync for safety
                existing.hashed_password = new_hash
                existing.login_attempts = 0
                existing.is_locked = False
                await session.flush()
                logger.info("Admin password updated for: %s", settings.ADMIN_EMAIL)
            else:
                logger.info("Default admin user already exists: %s", settings.ADMIN_EMAIL)
            return

        admin = AdminUser(
            email=settings.ADMIN_EMAIL,
            display_name="System Administrator",
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            role=AdminRole.super_admin,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        logger.info(
            "Default admin user created: %s (role=%s)",
            settings.ADMIN_EMAIL,
            AdminRole.super_admin.value,
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: runs startup logic before yielding, shutdown after."""
    global _start_time

    # ── Startup ──
    _start_time = time.time()
    logger.info(
        "Starting %s v%s (%s)",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )

    # Initialise Sentry
    _init_sentry()

    # Initialise database tables (safe: CREATE TABLE IF NOT EXISTS — idempotent)
    try:
        await init_db()
        logger.info("Database tables initialised via Base.metadata.create_all")
    except Exception as exc:
        logger.warning("Database table initialisation note: %s", exc)

    # Ensure default admin user exists
    try:
        await _create_admin_user()
    except Exception as exc:
        logger.error("Failed to create default admin user: %s", exc)

    # Verify critical table exists; retry init_db if missing
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1 FROM admin_users LIMIT 1"))
        logger.info("admin_users table verified")
    except Exception:
        logger.warning("admin_users table missing — re-running init_db")
        try:
            await init_db()
            from app.models import AdminUser
            from app.utils.security import hash_password
            async with async_session_factory() as session:
                result = await session.execute(
                    __import__("sqlalchemy").select(AdminUser).where(AdminUser.email == settings.ADMIN_EMAIL)
                )
                existing = result.scalar_one_or_none()
                if not existing:
                    admin = AdminUser(
                        email=settings.ADMIN_EMAIL,
                        display_name="System Administrator",
                        hashed_password=hash_password(settings.ADMIN_PASSWORD),
                        role=__import__("app.models", fromlist=["AdminRole"]).AdminRole.super_admin,
                        is_active=True,
                    )
                    session.add(admin)
                    await session.commit()
                    logger.info("Default admin user created after table init")
        except Exception as e:
            logger.error("Table init retry failed: %s", e)
    
    logger.info("%s is ready", settings.APP_NAME)

    yield  # ── Application runs here ──

    # ── Shutdown ──
    logger.info("%s shutting down", settings.APP_NAME)


# ──────────────────────────────────────────────────────────────────────────────
# Exception Handlers
# ──────────────────────────────────────────────────────────────────────────────


def _error_response(
    status_code: int,
    error: str,
    detail: str | None = None,
    code: str | None = None,
    validation_errors: list[dict[str, Any]] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """Build a standard JSON error response matching the ErrorResponse schema."""
    body: dict[str, Any] = {
        "success": False,
        "error": error,
        "detail": detail,
        "code": code,
        "status_code": status_code,
        "validation_errors": validation_errors,
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(status_code=status_code, content=body)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle explicitly raised HTTPExceptions."""
    return _error_response(
        status_code=exc.status_code,
        error=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        detail=None,
        code=_http_status_code(exc.status_code),
        request_id=getattr(request.state, "request_id", None),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic request validation errors (422)."""
    errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", []))
        errors.append(
            {
                "field": field,
                "message": err.get("msg", "Validation error"),
                "code": err.get("type", "validation_error"),
            }
        )
    return _error_response(
        status_code=422,
        error="Validation error",
        detail="One or more fields failed validation",
        code="VALIDATION_ERROR",
        validation_errors=errors,
        request_id=getattr(request.state, "request_id", None),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions (500)."""
    logger.exception("Unhandled exception: %s", exc)
    # In production, do not leak stack traces
    detail = str(exc) if settings.DEBUG else "An internal error occurred"
    return _error_response(
        status_code=500,
        error="Internal server error",
        detail=detail,
        code="INTERNAL_ERROR",
        request_id=getattr(request.state, "request_id", None),
    )


def _http_status_code(status_code: int) -> str:
    """Map HTTP status codes to machine-readable error codes."""
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    return mapping.get(status_code, f"HTTP_{status_code}")


# ──────────────────────────────────────────────────────────────────────────────
# Middleware
# ──────────────────────────────────────────────────────────────────────────────


async def request_id_middleware(request: Request, call_next: Any) -> Response:
    """Attach a unique request ID (X-Request-ID) to every request/response.

    If the client sends an X-Request-ID header, it is forwarded; otherwise
    a new UUID is generated.
    """
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = req_id

    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


async def rate_limit_middleware(request: Request, call_next: Any) -> Response:
    """Apply per-IP rate limiting to all requests.

    Uses the in-memory rate limiter. The limit is configurable via
    ``settings.RATE_LIMIT_PER_MINUTE``.
    """
    # Skip rate limiting for health/metrics endpoints
    path = request.url.path
    if path in ("/api/health", "/api/metrics"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    limiter = get_rate_limiter()

    # More restrictive rate limit for auth endpoints
    if path.startswith("/api/v1/auth/"):
        max_req = settings.RATE_LIMIT_AUTH_PER_MINUTE
    else:
        max_req = settings.RATE_LIMIT_PER_MINUTE

    if not limiter.check(key=f"ip:{client_ip}", max_requests=max_req):
        return _error_response(
            status_code=429,
            error="Too many requests",
            detail=f"Rate limit exceeded. Max {max_req} requests per minute.",
            code="RATE_LIMIT_EXCEEDED",
            request_id=getattr(request.state, "request_id", None),
        )

    return await call_next(request)


async def request_timing_middleware(request: Request, call_next: Any) -> Response:
    """Measure and log request duration."""
    start = time.time()
    response: Response = await call_next(request)
    duration = time.time() - start
    # Log slow requests (> 5s) as warnings
    if duration > 5.0:
        logger.warning(
            "Slow request: %s %s took %.3fs",
            request.method,
            request.url.path,
            duration,
        )
    response.headers["X-Response-Time-Ms"] = str(round(duration * 1000, 2))
    return response


# ──────────────────────────────────────────────────────────────────────────────
# Prometheus Metrics
# ──────────────────────────────────────────────────────────────────────────────


async def metrics_endpoint(request: Request) -> Response:
    """Serve Prometheus metrics at ``/api/metrics``."""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        return Response(
            content="# Prometheus client not installed",
            media_type="text/plain; version=0.0.4",
        )


# ──────────────────────────────────────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────────────────────────────────────


async def health_check(request: Request) -> JSONResponse:
    """Return service health status."""
    db_status = "disconnected"
    try:
        from app.database import engine

        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
            db_status = "connected"
    except Exception as exc:
        logger.warning("Health check — database unreachable: %s", exc)
        db_status = "disconnected"

    uptime = time.time() - _start_time if _start_time else 0.0

    overall_status = "ok" if db_status == "connected" else "degraded"

    return JSONResponse(
        content={
            "status": overall_status,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": db_status,
            "redis": None,  # Placeholder — add Redis check when available
            "uptime_seconds": round(uptime, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


# ──────────────────────────────────────────────────────────────────────────────
# Application Factory
# ──────────────────────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Fintech lending platform — FastAPI backend",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
        contact={
            "name": "OrangeFi Engineering",
            "url": "https://orangefi.com",
            "email": "engineering@orangefi.com",
        },
        license_info={
            "name": "Proprietary",
            "url": "https://orangefi.com/license",
        },
    )

    # ── CORS Middleware ──
    origins = [
        o.strip()
        for o in settings.CORS_ORIGINS.split(",")
        if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
        max_age=600,
    )

    # ── Custom Middleware (order matters — outermost runs first) ──
    app.middleware("http")(request_timing_middleware)
    app.middleware("http")(rate_limit_middleware)
    app.middleware("http")(request_id_middleware)

    # ── Exception Handlers ──
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    app.add_exception_handler(Exception, general_exception_handler)

    # ── Routers ──
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(borrower_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(integrations_router, prefix="/api/v1")
    app.include_router(servicing_router, prefix="/api/v1")
    app.include_router(compliance_router, prefix="/api/v1")
    app.include_router(underwriting_router, prefix="/api/v1")
    app.include_router(agent_router, prefix="")

    # ── Direct Routes (outside router prefix) ──

    @app.get("/api/health", tags=["infrastructure"])
    async def _health_check(request: Request) -> JSONResponse:
        """Health check endpoint (also accessible via GET /api/health)."""
        return await health_check(request)

    @app.get("/api/metrics", tags=["infrastructure"])
    async def _metrics(request: Request) -> Response:
        """Prometheus metrics endpoint."""
        return await metrics_endpoint(request)

    @app.post("/api/init-db", tags=["infrastructure"])
    async def _init_db(request: Request) -> JSONResponse:
        """Force database table initialisation (admin-only, one-time)."""
        from app.utils.dependencies import get_current_admin
        try:
            admin = await get_current_admin(request)
        except Exception:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=403, content={"detail": "Admin auth required"})
        try:
            await init_db()
            return JSONResponse(content={"status": "ok", "message": "Tables initialised"})
        except Exception as exc:
            return JSONResponse(status_code=500, content={"status": "error", "detail": str(exc)})

    return app


# ──────────────────────────────────────────────────────────────────────────────
# Application instance (imported by uvicorn)
# ──────────────────────────────────────────────────────────────────────────────

app = create_app()
