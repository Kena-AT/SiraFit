import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from fastapi_csrf_protect import CsrfProtectConfig
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
    # Startup: create tables if they don't exist (dev convenience).
    # In production, rely on Alembic migrations exclusively.
    if settings.ENVIRONMENT in ("development", "testing"):
        from app.core.database import Base, engine

        Base.metadata.create_all(bind=engine)

    logger.info("app_started", event_type="startup")
    yield
    logger.info("app_stopped", event_type="shutdown")


@CsrfProtect.load_config
async def get_csrf_config():
    return CsrfProtectConfig(
        secret_key=settings.SECRET_KEY,
        cookie_samesite="lax",
        cookie_secure=settings.ENVIRONMENT == "production",
    )


# Initialize CSRF protection
csrf = CsrfProtect()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SiraFit API - Career automation platform",
    lifespan=lifespan,
)

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

# CSRF protection
app.add_middleware(
    CsrfProtect,
    config=get_csrf_config,
)

# Security headers (HSTS/CSP/etc.)
app.add_middleware(SecurityHeadersMiddleware)

# Prometheus metrics (outermost so it counts every request)
app.add_middleware(MetricsMiddleware)

# Include health checks
app.include_router(health_router, prefix="/health", tags=["health"])

# Include Prometheus metrics endpoint
app.include_router(metrics_router, tags=["metrics"])

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
