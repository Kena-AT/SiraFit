import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.router import api_router
from app.core.health import router as health_router
from app.core.logging import configure_logging
from app.core.middleware import RequestTimingMiddleware
from app.core.rate_limiting import add_rate_limit_headers
from starlette.middleware.base import BaseHTTPMiddleware

# Configure structured logging
configure_logging()
logger = structlog.get_logger("app")

# Ensure declarative base creates tables if Alembic isn't run yet (for simple dev)
# In production, Alembic handles this.
from app.core.database import Base, engine
Base.metadata.create_all(bind=engine)

# Automatically add missing columns to existing tables (dev helper)
# This avoids breaking existing databases when models grow new fields.
import sqlalchemy as sa
from sqlalchemy import inspect

def _ensure_columns():
    """Add any model columns missing from existing tables (safe for dev)."""
    try:
        inspector = inspect(engine)
        for table_name, table in Base.metadata.tables.items():
            existing = {c["name"] for c in inspector.get_columns(table_name)}
            for col in table.columns:
                if col.name not in existing:
                    col_type = col.type.compile(engine.dialect)
                    nullable = "NULL" if col.nullable else "NOT NULL"
                    default = ""
                    if col.default is not None:
                        default = f" DEFAULT {col.default.arg!r}"
                    ddl = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type} {nullable}{default}"
                    with engine.connect() as conn:
                        conn.execute(sa.text(ddl))
                        conn.commit()
                    logger.info("migration", table=table_name, column=col.name, ddl=ddl)
    except Exception:
        logger.warning("column_migration_skipped", exc_info=True)

_ensure_columns()


class RateLimitHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware to add rate limit headers to all responses."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add rate limit headers if they were set during request processing
        if hasattr(request.state, "rate_limit_remaining"):
            response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
            response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
            response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)
        
        return response


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SiraFit API - Career automation platform",
)

# Request timing middleware (added first = innermost)
app.add_middleware(RequestTimingMiddleware)

# Rate limit header middleware
app.add_middleware(RateLimitHeaderMiddleware)

# CORS middleware (added last = outermost — must be first to handle OPTIONS preflights)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include health checks
app.include_router(health_router, prefix="/health", tags=["health"])

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR, tags=["api"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to mask internal errors."""
    logger.error("unhandled_exception", path=request.url.path, method=request.method, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "A system error occurred. Please try again later."},
    )


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("app_started", event_type="startup")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("app_stopped", event_type="shutdown")
