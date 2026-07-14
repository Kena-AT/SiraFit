from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter()


@router.get("/live")
def health_live():
    """Liveness probe - checks if the service is running"""
    return {"status": "healthy", "service": "sirafit-api", "alive": True}


@router.get("/ready")
def health_ready(db: Session = Depends(get_db)):
    """Readiness probe - checks if the service can handle requests"""
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
