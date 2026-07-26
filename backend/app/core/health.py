"""
Health check endpoints for SiraFit.

Provides liveness and readiness probes, plus a comprehensive status endpoint
for system health monitoring.
"""

import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.services.agent_api import check_agent_api_connection

router = APIRouter()


class AgentAPIStatus(BaseModel):
    connected: bool
    source: str  # "env" | "settings_ui" | "none"
    provider: Optional[str] = None
    error: Optional[str] = None


class HealthStatusResponse(BaseModel):
    frontend: bool
    backend: bool
    database: bool
    deployment: bool
    agent_api: AgentAPIStatus
    checked_at: datetime
    color: str  # Color code for the overall status
    message: str  # Human-readable status message


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
        
        return HealthStatusResponse(
            frontend=frontend_healthy,
            backend=backend_healthy,
            database=database_healthy,
            deployment=deployment_healthy,
            agent_api=agent_api_status,
            checked_at=datetime.utcnow().isoformat(),
            color=color,
            message=message,
        )
        
    except Exception as e:
        # If we can't even run the health checks, return red
        return HealthStatusResponse(
            frontend=False,
            backend=False,
            database=False,
            deployment=False,
            agent_api=AgentAPIStatus(connected=False, source="none", error=str(e)),
            checked_at=datetime.utcnow().isoformat(),
            color="red",
            message="Health check failed",
        )


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
        return f"blend:{color1}:{color2}", f"{failing[0].replace('_', ' ').title()} and {failing[1].replace('_', ' ').title()} issues"
    
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