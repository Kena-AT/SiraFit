"""Structured AI Output service using Instructor (Sprint 7).

Provides type-safe, validated schema generation across multiple LLM providers:
- Built on top of `ai_keys.build_candidates` provider fallback resolution
- Bounded retry budget for validation errors
- Telemetry & audit logging to `AICompletion` and `AICompletionAttempt`
- Prometheus metric integration with granular failure classification
- Error isolation: Telemetry failures never crash user generation
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

import instructor
from openai import AsyncOpenAI
from app.core.metrics import (
    AI_COMPLETIONS_TOTAL,
    AI_COMPLETION_DURATION_SECONDS,
    AI_COMPLETION_FAILURES_TOTAL,
    AI_VALIDATION_RETRIES_TOTAL,
    SIRAFIT_AI_REQUESTS_TOTAL,
    SIRAFIT_AI_REQUEST_DURATION_SECONDS,
    SIRAFIT_AI_TOKENS_TOTAL,
)
from app.models.ai_completion import AICompletion, AICompletionAttempt

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Provider endpoints configuration
_PROVIDER_CONFIG: dict[str, dict[str, Any]] = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "mode": instructor.Mode.JSON,
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "mode": instructor.Mode.TOOLS,
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "mode": instructor.Mode.TOOLS,
        "default_headers": {
            "HTTP-Referer": "https://sirafit.com",
            "X-Title": "SiraFit",
        },
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
    },
    "grok": {
        "base_url": "https://api.x.ai/v1",
        "mode": instructor.Mode.TOOLS,
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "mode": instructor.Mode.TOOLS,
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "mode": instructor.Mode.TOOLS,
    },
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def classify_ai_exception(exc: Exception) -> str:
    """Classify an exception into bounded, high-cardinality-safe error codes."""
    if isinstance(exc, ValidationError):
        return "validation_error"

    exc_name = type(exc).__name__.lower()
    exc_str = str(exc).lower()

    if "validation" in exc_str or "validationerror" in exc_name:
        return "validation_error"
    if "ratelimit" in exc_name or "429" in exc_str or "rate limit" in exc_str:
        return "rate_limit"
    if "timeout" in exc_name or "timeouterror" in exc_name or "timed out" in exc_str:
        return "timeout"
    if (
        "auth" in exc_name
        or "authentication" in exc_name
        or "401" in exc_str
        or "403" in exc_str
        or "invalid api key" in exc_str
        or "unauthorized" in exc_str
    ):
        return "auth_error"
    if "schema" in exc_str or "json" in exc_str:
        return "schema_error"

    return "unknown"


def get_instructor_client(provider: str, api_key: str) -> Any:
    """Instantiate and return an Instructor-wrapped async client."""
    prov = (provider or "").lower()

    if prov == "anthropic":
        try:
            from anthropic import AsyncAnthropic

            anthropic_client = AsyncAnthropic(api_key=api_key)
            return instructor.from_anthropic(anthropic_client)
        except Exception as err:
            logger.debug("Failed to initialize native anthropic instructor: %s", err)
            # Fall back to OpenAI client wrapper if applicable
            raise

    cfg = _PROVIDER_CONFIG.get(prov, {})
    base_url = cfg.get("base_url", "https://api.openai.com/v1")
    mode = cfg.get("mode", instructor.Mode.TOOLS)
    default_headers = cfg.get("default_headers")

    openai_client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        default_headers=default_headers,
        timeout=60.0,
    )
    return instructor.from_openai(openai_client, mode=mode)


def _safe_record_telemetry(
    db: Optional[Session],
    generation_id: str,
    user_id: Optional[uuid.UUID],
    operation: str,
    provider: str,
    model: str,
    response_model_name: str,
    status: str,
    total_duration_ms: int,
    attempts_data: list[dict[str, Any]],
    total_tokens: Optional[int] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
) -> Optional[AICompletion]:
    """Record completion and attempts to database without failing generation on DB errors."""
    if db is None:
        return None

    try:
        completion = AICompletion(
            id=uuid.uuid4(),
            generation_id=generation_id,
            user_id=user_id,
            operation=operation,
            provider=provider,
            model=model,
            response_model=response_model_name,
            status=status,
            attempt_count=len(attempts_data),
            duration_ms=total_duration_ms,
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            created_at=_utcnow(),
            completed_at=_utcnow(),
        )
        db.add(completion)
        db.flush()

        for att in attempts_data:
            attempt_record = AICompletionAttempt(
                id=uuid.uuid4(),
                completion_id=completion.id,
                attempt_number=att.get("attempt_number", 1),
                provider=att.get("provider", provider),
                model=att.get("model", model),
                status=att.get("status", "failed"),
                failure_code=att.get("failure_code"),
                validation_errors=att.get("validation_errors"),
                duration_ms=att.get("duration_ms", 0),
                created_at=_utcnow(),
            )
            db.add(attempt_record)

        db.commit()
        return completion
    except Exception as db_err:
        logger.error(
            "Failed to record AI completion telemetry (Issue #53): %s",
            db_err,
            exc_info=True,
        )
        try:
            db.rollback()
        except Exception:
            pass
        return None


async def structured_completion_with_fallback(
    operation: str,
    response_model: Type[T],
    messages: list[dict[str, str]],
    candidates: list[tuple[str, str, str]],
    db: Optional[Session] = None,
    user_id: Optional[uuid.UUID] = None,
    generation_id: Optional[str] = None,
    max_retries: int = 2,
    temperature: float = 0.1,
) -> tuple[T, Optional[AICompletion]]:
    """Execute a structured completion across candidate providers with failover and auditing.

    Args:
        operation: Name of the AI operation (e.g. 'job_analysis', 'resume_generation').
        response_model: Pydantic model class for structured parsing.
        messages: List of message dicts (e.g. [{'role': 'system', ...}, {'role': 'user', ...}]).
        candidates: List of (provider, model, api_key) candidate tuples.
        db: Optional database session for audit records.
        user_id: Optional user ID for audit attribution.
        generation_id: Correlation ID (defaults to newly generated UUID4).
        max_retries: Bounded retries for schema validation per candidate.
        temperature: Sampling temperature.

    Returns:
        A tuple of (parsed_output_model, ai_completion_record_or_None).
    """
    if not candidates:
        raise RuntimeError(f"No AI candidates provided for operation '{operation}'")

    gen_id = generation_id or str(uuid.uuid4())
    start_total = time.perf_counter()
    attempts_data: list[dict[str, Any]] = []
    last_exc: Optional[Exception] = None

    for attempt_idx, (provider, model, api_key) in enumerate(candidates, start=1):
        attempt_start = time.perf_counter()
        attempt_status = "failed"
        failure_code = None
        val_errors = None

        logger.info(
            "Attempting structured AI completion: operation=%s, candidate=%d/%d, provider=%s, model=%s",
            operation,
            attempt_idx,
            len(candidates),
            provider,
            model,
        )

        try:
            client = get_instructor_client(provider, api_key)

            # Request structured output via instructor
            result = await client.chat.completions.create(
                model=model,
                response_model=response_model,
                messages=messages,
                max_retries=max_retries,
                temperature=temperature,
            )

            attempt_duration_ms = int((time.perf_counter() - attempt_start) * 1000)
            total_duration_ms = int((time.perf_counter() - start_total) * 1000)

            # Record attempt success
            attempts_data.append({
                "attempt_number": attempt_idx,
                "provider": provider,
                "model": model,
                "status": "success",
                "failure_code": None,
                "validation_errors": None,
                "duration_ms": attempt_duration_ms,
            })

            # Record metrics
            status_label = "success" if attempt_idx == 1 else "fallback"
            AI_COMPLETIONS_TOTAL.labels(
                operation=operation,
                provider=provider,
                model=model,
                status=status_label,
            ).inc()
            AI_COMPLETION_DURATION_SECONDS.labels(
                operation=operation,
                provider=provider,
            ).observe(attempt_duration_ms / 1000.0)

            # Record Sprint 15 AI metrics
            SIRAFIT_AI_REQUESTS_TOTAL.labels(
                provider=provider,
                model=model,
                status=status_label,
                operation=operation,
            ).inc()
            SIRAFIT_AI_REQUEST_DURATION_SECONDS.labels(
                provider=provider,
                operation=operation,
            ).observe(attempt_duration_ms / 1000.0)

            # Extract token counts if available
            raw_completion = getattr(result, "_raw_response", None)
            total_tokens = None
            prompt_tokens = None
            completion_tokens = None
            if raw_completion and hasattr(raw_completion, "usage") and raw_completion.usage:
                usage = raw_completion.usage
                total_tokens = getattr(usage, "total_tokens", None)
                prompt_tokens = getattr(usage, "prompt_tokens", None)
                completion_tokens = getattr(usage, "completion_tokens", None)

                if prompt_tokens:
                    SIRAFIT_AI_TOKENS_TOTAL.labels(
                        provider=provider, model=model, direction="prompt"
                    ).inc(prompt_tokens)
                if completion_tokens:
                    SIRAFIT_AI_TOKENS_TOTAL.labels(
                        provider=provider, model=model, direction="completion"
                    ).inc(completion_tokens)

            # Record audit telemetry in DB
            completion_rec = _safe_record_telemetry(
                db=db,
                generation_id=gen_id,
                user_id=user_id,
                operation=operation,
                provider=provider,
                model=model,
                response_model_name=response_model.__name__,
                status=status_label,
                total_duration_ms=total_duration_ms,
                attempts_data=attempts_data,
                total_tokens=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

            return result, completion_rec

        except Exception as exc:
            attempt_duration_ms = int((time.perf_counter() - attempt_start) * 1000)
            last_exc = exc
            failure_code = classify_ai_exception(exc)

            if isinstance(exc, ValidationError):
                val_errors = exc.errors()
                AI_VALIDATION_RETRIES_TOTAL.labels(
                    operation=operation,
                    provider=provider,
                ).inc()

            logger.warning(
                "Structured completion failed for %s/%s (%s): %s",
                provider,
                model,
                failure_code,
                exc,
            )

            AI_COMPLETION_FAILURES_TOTAL.labels(
                operation=operation,
                provider=provider,
                failure_code=failure_code,
            ).inc()

            attempts_data.append({
                "attempt_number": attempt_idx,
                "provider": provider,
                "model": model,
                "status": "failed",
                "failure_code": failure_code,
                "validation_errors": val_errors,
                "duration_ms": attempt_duration_ms,
            })

    # All candidates exhausted
    total_duration_ms = int((time.perf_counter() - start_total) * 1000)
    last_prov = candidates[-1][0] if candidates else "unknown"
    last_model = candidates[-1][1] if candidates else "unknown"

    AI_COMPLETIONS_TOTAL.labels(
        operation=operation,
        provider=last_prov,
        model=last_model,
        status="failed",
    ).inc()

    _safe_record_telemetry(
        db=db,
        generation_id=gen_id,
        user_id=user_id,
        operation=operation,
        provider=last_prov,
        model=last_model,
        response_model_name=response_model.__name__,
        status="failed",
        total_duration_ms=total_duration_ms,
        attempts_data=attempts_data,
    )

    if last_exc is not None:
        raise last_exc
    raise RuntimeError(f"All AI candidates failed for operation '{operation}'")
