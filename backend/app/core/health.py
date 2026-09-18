"""
Health check endpoints for SiraFit.

Provides liveness and readiness probes, plus a comprehensive status endpoint
for system health monitoring.
"""

import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db, get_pool_stats, engine
from app.core.config import settings
from app.services.agent_api import check_agent_api_connection

router = APIRouter()


class AgentAPIStatus(BaseModel):
    connected: bool
    source: str  # "env" | "settings_ui" | "none"
    provider: Optional[str] = None
    error: Optional[str] = None


class StatusState(str):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class SystemStatusResponse(BaseModel):
    """Sanitized public system status response (Sprint 15).

    Does not expose internal pool statistics, disk paths, or hostnames.
    """

    overall: str  # "healthy" | "degraded" | "failed" | "unknown"
    api: str
    database: str
    redis: str
    background_jobs: str
    last_checked: datetime


class HealthStatusResponse(BaseModel):
    frontend: bool
    backend: bool
    database: bool
    deployment: bool
    agent_api: AgentAPIStatus
    checked_at: datetime
    color: str  # Color code for the overall status
    message: str  # Human-readable status message
    pool_utilization_pct: Optional[float] = None  # Pool exhaustion signal (Phase 2.5)
    worker_healthy: Optional[bool] = None  # Celery worker liveness (Phase 3.7)
    # Sanitized system status structure for backward/forward compatibility
    system_status: Optional[SystemStatusResponse] = None


@router.get("/live")
def health_live():
    """Liveness probe - checks if the service is running."""
    return {"status": "healthy", "service": "sirafit-api", "alive": True}


@router.get("/ready")
def health_ready(db: Session = Depends(get_db)):
    """Readiness probe - checks if the service can handle requests."""
    try:
        # Check database connection
        result = db.execute(text("SELECT 1"))
        result.fetchone()

        # Check Redis (if available)
        redis_ready = True
        try:
            import redis

            r = redis.from_url("redis://localhost:6379/0")
            r.ping()
        except Exception:
            redis_ready = False  # Redis is optional for basic health

        return {
            "status": "ready",
            "service": "sirafit-api",
            "database": "connected",
            "redis": "connected" if redis_ready else "disabled",
            "ready": True,
        }
    except Exception as e:
        return {
            "status": "not ready",
            "service": "sirafit-api",
            "database": "error",
            "error": str(e),
            "ready": False,
        }


@router.get("/status", response_model=HealthStatusResponse)
def health_status(db: Session = Depends(get_db)):
    """
    Comprehensive health status check for the entire system.

    Checks:
    - Frontend: Can the frontend reach this endpoint?
    - Backend: Is this service running?
    - Database: Can we query the database?
    - Deployment: Is the deployment healthy?
    - Agent API: Is the model API connection working?

    Returns a color-coded status based on the health checks.
    """
    try:
        # 1. Backend check (always true if we're running this endpoint)
        backend_healthy = True

        # 2. Database check
        database_healthy = _check_database(db)

        # 3. Deployment check
        deployment_healthy = _check_deployment()

        # 4. Agent API check
        agent_api_status = check_agent_api_connection()

        # 5. Pool exhaustion monitoring (Phase 2.5)
        pool_stats = get_pool_stats() if engine else None

        # 5. Frontend check (self-reported by client, but we include it in the response)
        # The frontend will set this based on its own health
        frontend_healthy = True  # Placeholder - frontend will override

        # Determine overall color based on health checks
        color, message = _determine_status_color(
            frontend_healthy,
            backend_healthy,
            database_healthy,
            deployment_healthy,
            agent_api_status.connected,
        )

        pool_utilization_pct = pool_stats.get("utilization_pct") if pool_stats else None

        # Celery worker liveness (Phase 3.7) — None in dev/CI, True/False in prod.
        worker_healthy = _check_worker()
        redis_healthy = _check_redis()

        # Build sanitized SystemStatusResponse (Sprint 15)
        overall_state = StatusState.HEALTHY
        if not database_healthy or (worker_healthy is False):
            overall_state = (
                StatusState.DEGRADED
                if (database_healthy or worker_healthy is not False)
                else StatusState.FAILED
            )

        sanitized_status = SystemStatusResponse(
            overall=overall_state,
            api=StatusState.HEALTHY if backend_healthy else StatusState.FAILED,
            database=StatusState.HEALTHY if database_healthy else StatusState.FAILED,
            redis=StatusState.HEALTHY if redis_healthy else StatusState.DEGRADED,
            background_jobs=StatusState.HEALTHY
            if (worker_healthy is not False)
            else StatusState.DEGRADED,
            last_checked=datetime.utcnow(),
        )

        return HealthStatusResponse(
            frontend=frontend_healthy,
            backend=backend_healthy,
            database=database_healthy,
            deployment=deployment_healthy,
            agent_api=agent_api_status.model_dump(),
            checked_at=datetime.utcnow(),
            color=color,
            message=message,
            # Pool exhaustion monitoring (Phase 2.5)
            pool_utilization_pct=pool_utilization_pct,
            # Celery worker liveness (Phase 3.7)
            worker_healthy=worker_healthy,
            system_status=sanitized_status,
        )

    except Exception as e:
        # If we can't even run the health checks, return failed
        now = datetime.utcnow()
        return HealthStatusResponse(
            frontend=False,
            backend=False,
            database=False,
            deployment=False,
            agent_api=AgentAPIStatus(
                connected=False, source="none", error=str(e)
            ).model_dump(),
            checked_at=now,
            color="red",
            message="Health check failed",
            worker_healthy=None,
            system_status=SystemStatusResponse(
                overall=StatusState.FAILED,
                api=StatusState.FAILED,
                database=StatusState.UNKNOWN,
                redis=StatusState.UNKNOWN,
                background_jobs=StatusState.UNKNOWN,
                last_checked=now,
            ),
        )


@router.get("/system-status", response_model=SystemStatusResponse)
def get_system_status(db: Session = Depends(get_db)):
    """Sanitized public system status endpoint (Sprint 15).

    Returns high-level service status without leaking internal metrics, pool counts,
    or server infrastructure details.
    """
    database_healthy = _check_database(db)
    redis_healthy = _check_redis()
    worker_healthy = _check_worker()

    if database_healthy and redis_healthy and (worker_healthy is not False):
        overall = StatusState.HEALTHY
    elif database_healthy or (worker_healthy is not False):
        overall = StatusState.DEGRADED
    else:
        overall = StatusState.FAILED

    return SystemStatusResponse(
        overall=overall,
        api=StatusState.HEALTHY,
        database=StatusState.HEALTHY if database_healthy else StatusState.FAILED,
        redis=StatusState.HEALTHY if redis_healthy else StatusState.DEGRADED,
        background_jobs=StatusState.HEALTHY
        if (worker_healthy is not False)
        else StatusState.DEGRADED,
        last_checked=datetime.utcnow(),
    )


def _check_redis() -> bool:
    """Check Redis connectivity with strict 1.0s timeout."""
    try:
        from app.core.redis_client import get_redis_client

        client = get_redis_client()
        if client:
            client.ping()
            return True
        return False
    except Exception:
        return False


def _check_database(db: Session) -> bool:
    """Check if the database is reachable and responsive."""
    try:
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        return True
    except Exception:
        return False


def _check_deployment() -> bool:
    """
    Check if the deployment is healthy.

    This implementation assumes we're using a deployment platform that
    provides environment variables like COMMIT_SHA or DEPLOYMENT_ID.

    For production, you'd want to implement platform-specific checks:
    - Vercel: Use the Vercel API to check deployment status
    - Render/Fly: Use their respective APIs
    - Self-hosted: Compare against a known good version
    """
    try:
        # Check if we have deployment info available
        # This is a simplified check - in production, you'd want to verify
        # the deployment status against the platform's API
        if os.getenv("COMMIT_SHA") or os.getenv("DEPLOYMENT_ID"):
            return True
        return True  # Assume healthy if no specific check is implemented
    except Exception:
        return False


def _check_worker() -> Optional[bool]:
    """Check whether at least one Celery worker is alive.

    Returns ``None`` when the check is intentionally skipped (local dev / CI,
    where no worker runs), and ``True``/``False`` in production. Celery is
    lazy-imported so the worker runtime is never pulled into the API process
    at import time, and any failure degrades to ``False`` rather than raising.
    """
    if settings.ENVIRONMENT in ("testing", "test", "development"):
        return None
    try:
        from app.worker.celery_app import celery_app

        inspect = celery_app.control.inspect(timeout=1.0)
        if inspect is None:
            return False
        return bool(inspect.active())
    except Exception:
        return False


def _determine_status_color(
    frontend: bool,
    backend: bool,
    database: bool,
    deployment: bool,
    agent_api: bool,
) -> tuple[str, str]:
    """
    Determine the overall status color based on the health checks.

    Follows the priority-based color mapping from the spec:
    - All healthy: green
    - Only backend failing: blue
    - Only frontend failing: yellow
    - Only database failing: purple
    - Only deployment failing: purple
    - Exactly 2 failing: blended color
    - 3+ failing: red

    Returns:
        tuple: (color, message)
    """
    components = {
        "frontend": frontend,
        "backend": backend,
        "database": database,
        "deployment": deployment,
        "agent_api": agent_api,
    }

    failing = [name for name, healthy in components.items() if not healthy]

    # All healthy
    if not failing:
        return "green", "All systems operational"

    # Single component failing
    if len(failing) == 1:
        component = failing[0]
        if component == "backend":
            return "blue", "Backend service issue"
        elif component == "frontend":
            return "yellow", "Frontend service issue"
        elif component in ["database", "deployment"]:
            return "purple", f"{component.replace('_', ' ').title()} issue"
        elif component == "agent_api":
            return "orange", "Agent API connection issue"

    # Two components failing
    if len(failing) == 2:
        # For two failures, use a split/gradient dot showing both colors
        # We return a special "blend" color that the frontend can interpret
        # as a gradient between the two component colors
        color1 = _get_component_color(failing[0])
        color2 = _get_component_color(failing[1])
        return (
            f"blend:{color1}:{color2}",
            f"{failing[0].replace('_', ' ').title()} and {failing[1].replace('_', ' ').title()} issues",
        )

    # Three or more failing
    return "red", "Multiple system issues"


def _get_component_color(component: str) -> str:
    """Get the color for a single failing component."""
    if component == "backend":
        return "blue"
    elif component == "frontend":
        return "yellow"
    elif component in ["database", "deployment"]:
        return "purple"
    elif component == "agent_api":
        return "orange"
    return "gray"  # fallback
