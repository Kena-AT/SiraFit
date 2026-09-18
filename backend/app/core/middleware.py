import time
import uuid
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.observability.tracing import get_current_trace_context


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware to add request timing, trace correlation, and logging."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        # Get or create request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Extract active trace/span context if available
        trace_id, span_id = get_current_trace_context()

        # Bind context variables for log correlation
        context_dict = {"request_id": request_id}
        if trace_id:
            context_dict["trace_id"] = trace_id
        if span_id:
            context_dict["span_id"] = span_id

        structlog.contextvars.bind_contextvars(**context_dict)

        try:
            response = await call_next(request)
        except Exception as exc:
            # Calculate duration even on unhandled failure
            duration_ms = (time.time() - start_time) * 1000
            logger = structlog.get_logger("request")
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(exc),
                duration_ms=round(duration_ms, 2),
                request_id=request_id,
            )
            raise
        finally:
            structlog.contextvars.unbind_contextvars(
                "request_id", "trace_id", "span_id"
            )

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

        # Add response headers
        response.headers["X-Request-ID"] = request_id
        if trace_id:
            response.headers["X-Trace-ID"] = trace_id

        return response
