import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from app.core.config import settings
from app.api.router import api_router
from app.core.health import router as health_router
from app.core.logging import configure_logging
from app.core.middleware import RequestTimingMiddleware
from app.core.rate_limiting import RateLimitMiddleware
from app.core.metrics import router as metrics_router, MetricsMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Configure structured logging
configure_logging()
logger = structlog.get_logger("app")


class RateLimitHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware to add rate limit headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add rate limit headers if they were set during request processing
        if hasattr(request.state, "rate_limit_remaining"):
            response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
            response.headers["X-RateLimit-Remaining"] = str(
                request.state.rate_limit_remaining
            )
            response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add baseline security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissive enough for a Vite SPA talking to a same-origin or https API.
        # Review against the real production origin before relying on it.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https://*.sirafit.com; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' https://*.sirafit.com; "
            "connect-src 'self' https://*.sirafit.com https://api.sirafit.com; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "object-src 'none'"
        )
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    from app.core.redis_client import get_redis_client
    redis_client = get_redis_client()
    if not redis_client:
        if settings.ENVIRONMENT == "production":
            logger.error("redis_connection_required_failed", extra={"redis_url": settings.REDIS_URL})
            raise RuntimeError(f"FATAL: Redis connection could not be established at {settings.REDIS_URL}. Redis is required in production.")
        else:
            logger.warning("redis_unavailable_using_memory_cache", extra={"redis_url": settings.REDIS_URL})
    else:
        try:
            redis_client.ping()
        except Exception as e:
            if settings.ENVIRONMENT == "production":
                logger.error("redis_ping_failed", extra={"error": str(e)})
                raise RuntimeError(f"FATAL: Redis ping failed at {settings.REDIS_URL}: {e}")
            else:
                logger.warning("redis_ping_failed_using_memory_cache", extra={"error": str(e)})

    # Startup: create tables if they don't exist (dev convenience).
    # In production, rely on Alembic migrations exclusively.
    if settings.ENVIRONMENT in ("development", "testing"):
        from app.core.database import Base, engine

        Base.metadata.create_all(bind=engine)

    logger.info("app_started", event_type="startup")
    yield
    logger.info("app_stopped", event_type="shutdown")


from pydantic import BaseModel

class CsrfSettings(BaseModel):
    secret_key: str = settings.SECRET_KEY
    cookie_samesite: str = "none"
    cookie_secure: bool = True

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SiraFit API - Career automation platform",
    lifespan=lifespan,
)

# GZip compression middleware for payloads > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request timing middleware (added first = innermost)
app.add_middleware(RequestTimingMiddleware)

# Rate limit header middleware
app.add_middleware(RateLimitHeaderMiddleware)

# Redis-backed rate limiting (no-op outside production)
app.add_middleware(RateLimitMiddleware)

# CORS middleware (added last = outermost — must be first to handle OPTIONS preflights)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers (HSTS/CSP/etc.)
app.add_middleware(SecurityHeadersMiddleware)

# Prometheus metrics (outermost so it counts every request)
app.add_middleware(MetricsMiddleware)

# Include Prometheus metrics endpoint
app.include_router(metrics_router, tags=["metrics"])

# Health checks at /health/* for Docker/k8s probes (live, ready) and the
# same router also mounted under /api/v1/* via api_router for the SPA
# (which calls /api/v1/health/status). Both prefixes share the same routes.
app.include_router(health_router, prefix="/health", tags=["health"])

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR, tags=["api"])


@app.exception_handler(CsrfProtectError)
async def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    """Handle CSRF protection errors."""
    logger.warning(
        "csrf_protect_error",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )
    return JSONResponse(
        status_code=403,
        content={"detail": "CSRF token validation failed."},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to mask internal errors."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "A system error occurred. Please try again later."},
    )
