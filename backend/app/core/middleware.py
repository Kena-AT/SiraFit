import time
import uuid
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware to add request timing and logging"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Start timing
        start_time = time.time()

        # Get or create request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Add request ID to context
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log request completion
        logger = structlog.get_logger("request")
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            request_id=request_id,
        )

        # Clean up context
        structlog.contextvars.unbind_contextvars("request_id")

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
