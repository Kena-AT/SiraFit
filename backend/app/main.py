import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.router import api_router
from app.core.health import router as health_router
from app.core.logging import configure_logging
from app.core.middleware import RequestTimingMiddleware

# Configure structured logging
configure_logging()
logger = structlog.get_logger("app")

# Ensure declarative base creates tables if Alembic isn't run yet (for simple dev)
# In production, Alembic handles this.
from app.core.database import Base, engine
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SiraFit API - Career automation platform",
)

# Request timing middleware (added first = innermost)
app.add_middleware(RequestTimingMiddleware)

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
