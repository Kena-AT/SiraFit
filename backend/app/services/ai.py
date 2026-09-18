"""
AI service for job analysis.
Supports Gemini and OpenRouter providers with:
  - Prompt versioning via PROMPTS registry
  - Pydantic-validated structured output
  - Retry logic with exponential backoff
"""

import json
import asyncio
import logging
from typing import Optional
from pydantic import BaseModel, ValidationError

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt versioning registry
# ---------------------------------------------------------------------------

CURRENT_PROMPT_VERSION = "v1"

PROMPTS: dict[str, str] = {
    "v1": """You are an expert technical recruiter. Analyze the job description and candidate profile below.
Return ONLY a valid JSON object with this exact structure (no markdown, no extra text):
{
  "score": 0-100,
  "summary": "2-3 sentence summary of the role and fit",
  "pros": ["strength 1", "strength 2"],
  "cons": ["weakness 1", "weakness 2"],
  "skills_gap": ["missing skill 1", "missing skill 2"],
  "key_requirements": ["requirement 1", "requirement 2"],
  "seniority": "Junior|Mid|Senior|Staff|Lead|Director"
}

Rules:
- score: integer 0-100 representing candidate match quality
- pros/cons/skills_gap/key_requirements: arrays of short strings (max 6 items each)
- seniority: one of the exact values listed above
- Do NOT include any text before or after the JSON object""",
}


# ---------------------------------------------------------------------------
# Structured output schema (validated with Pydantic)
# ---------------------------------------------------------------------------


class AnalysisOutput(BaseModel):
    score: int
    summary: str
    pros: list[str]
    cons: list[str]
    skills_gap: list[str]
    key_requirements: list[str] = []
    seniority: str = "Mid"

    def model_post_init(self, __context):
        # Clamp score to 0-100
        self.score = max(0, min(100, self.score))
        # Limit list lengths to 6 items
        self.pros = self.pros[:6]
        self.cons = self.cons[:6]
        self.skills_gap = self.skills_gap[:6]
        self.key_requirements = self.key_requirements[:6]


def _parse_and_validate(text: str) -> AnalysisOutput:
    """Parse AI text output and validate against AnalysisOutput schema."""
    clean = text.strip()
    # Strip markdown code fences if present
    if clean.startswith("```"):
        clean = clean.split("```")[-2] if "```" in clean[3:] else clean[3:]
        if clean.lower().startswith("json"):
            clean = clean[4:]
        clean = clean.strip()
    data = json.loads(clean)
    return AnalysisOutput.model_validate(data)


# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------


def _is_retryable(exc) -> bool:
    """Classify whether an AI failure is worth retrying.

    Permanent errors (auth failure, unknown provider, malformed output) are NOT
    retried — they will not succeed on a later attempt and should instead
    trigger a fallback to a different provider/model.
    """
    if isinstance(exc, ValueError):
        return False  # unknown provider, etc.
    if isinstance(exc, (json.JSONDecodeError, ValidationError)):
        return False  # malformed model output — fall back, don't retry
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code if exc.response is not None else 0
        if code in (401, 403):
            return False  # auth/permission — permanent for this key
        return code >= 500 or code == 429  # server busy / rate limited
    if isinstance(exc, (httpx.TransportError, httpx.TimeoutException)):
        return True  # network blip
    return False


async def _with_retry(fn, max_attempts: int = 3):
    """Call async fn up to max_attempts times with exponential backoff.

    Only retryable errors (see ``_is_retryable``) are retried; permanent errors
    propagate immediately so callers can fall back to another candidate.
    """
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return await fn()
        except Exception as e:
            last_exc = e
            if not _is_retryable(e):
                raise
            logger.warning(f"AI call error attempt {attempt + 1}: {e}")
            if attempt < max_attempts - 1:
                await asyncio.sleep(2**attempt)  # 1s, 2s, 4s
    raise last_exc


async def complete_with_fallback(
    prompt: str,
    candidates: list,
    system: Optional[str] = None,
    max_tokens: int = 1024,
    parse_fn=None,
):
    """Try each (provider, model, key) candidate in order, returning first success.

    ``candidates`` is the ordered list from ``app.services.ai_keys.build_candidates``.
    Each candidate is attempted with retry/backoff for transient errors; permanent
    errors or exhaustion move on to the next candidate. ``parse_fn`` (if given) is
    applied to the successful candidate's text and its result returned.

    Raises the last error if every candidate fails.
    """
    last_exc = None
    for provider, model, api_key in candidates:
        try:
            text = await _with_retry(
                lambda: complete(prompt, api_key, provider, model, system, max_tokens),
                max_attempts=2,
            )
            return parse_fn(text) if parse_fn is not None else text
        except Exception as exc:
            logger.warning(
                "AI candidate %s/%s failed; trying next: %s", provider, model, exc
            )
            last_exc = exc
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("No AI candidates were available")


# ---------------------------------------------------------------------------
# Raw-text completion (reusable across job analysis, resume & cover-letter gen)
# ---------------------------------------------------------------------------

# Per-provider default model used when a caller doesn't pass one.
DEFAULT_MODELS: dict[str, str] = {
    "gemini": "gemini-1.5-flash",
    "anthropic": "claude-3-5-sonnet-20240620",
    "openrouter": "openai/gpt-4o-mini",
    "openai": "gpt-4o-mini",
    "grok": "grok-beta",
    "mistral": "mistral-large-latest",
    "nvidia": "meta/llama-3.1-405b-instruct",
}

# OpenAI-compatible providers share one chat-completions client; keyed by id.
_OPENAI_COMPATIBLE: dict[str, dict] = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "name": "OpenRouter",
        "extra": {"HTTP-Referer": "https://sirafit.com", "X-Title": "SiraFit"},
    },
    "openai": {"base_url": "https://api.openai.com/v1", "name": "OpenAI"},
    "grok": {"base_url": "https://api.x.ai/v1", "name": "Grok"},
    "mistral": {"base_url": "https://api.mistral.ai/v1", "name": "Mistral"},
    "nvidia": {"base_url": "https://integrate.api.nvidia.com/v1", "name": "Nvidia NIM"},
}


async def complete(
    prompt: str,
    api_key: str,
    provider: str,
    model: Optional[str] = None,
    system: Optional[str] = None,
    max_tokens: int = 1024,
) -> str:
    """
    Send a prompt to the given provider and return the raw text response.

    This is the single entry point for "generate text with the configured AI".
    Job analysis wraps it with JSON validation; resume/cover-letter generation
    call it directly.

    Raises on failure (callers wrap in `_with_retry` or handle as needed).
    """
    provider = (provider or "").lower()
    model = model or DEFAULT_MODELS.get(provider, "")

    if provider == "gemini":
        return await _complete_gemini(prompt, api_key, model, system)
    if provider == "anthropic":
        return await _complete_anthropic(prompt, api_key, model, system, max_tokens)
    if provider in _OPENAI_COMPATIBLE:
        cfg = _OPENAI_COMPATIBLE[provider]
        return await _complete_openai_compatible(
            prompt,
            api_key,
            cfg["base_url"],
            model,
            system,
            cfg["name"],
            cfg.get("extra"),
        )
    raise ValueError(f"Unknown AI provider: {provider!r}")


async def _complete_gemini(
    prompt: str, api_key: str, model: str, system: Optional[str]
) -> str:
    import google.generativeai as genai

    model_name = (
        "models/gemini-1.5-pro" if "pro" in model.lower() else "models/gemini-1.5-flash"
    )
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    genai.configure(api_key=api_key)
    gen_model = genai.GenerativeModel(model_name)
    response = gen_model.generate_content(full_prompt)
    return response.text


async def _complete_anthropic(
    prompt: str, api_key: str, model: str, system: Optional[str], max_tokens: int
) -> str:
    from anthropic import AsyncAnthropic

    async with AsyncAnthropic(api_key=api_key) as client:
        message = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text


async def _complete_openai_compatible(
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
    system: Optional[str],
    provider_name: str,
    extra_headers: Optional[dict] = None,
) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json={"model": model, "messages": messages, "temperature": 0.1},
        )
        if response.status_code != 200:
            logger.error(
                f"{provider_name} error ({response.status_code}): {response.text}"
            )
        response.raise_for_status()
        data = response.json()
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------


async def analyze_job(
    prompt_context: str,
    api_key: str,
    provider: str,
    model: Optional[str] = None,
    prompt_version: str = CURRENT_PROMPT_VERSION,
) -> AnalysisOutput:
    """Generic dispatcher for job analysis across multiple providers.

    Tries the single (provider, model, key) given; kept for callers that have
    already resolved one candidate (e.g. scoring.py). New callers should build
    a candidate list with ``ai_keys.build_candidates`` and use
    ``analyze_job_with_fallback`` to get cross-provider resilience.
    """
    provider = (provider or "").lower()
    if provider not in DEFAULT_MODELS:
        logger.warning(
            f"Unknown provider: {provider}, falling back to keyword analysis"
        )
        return keyword_fallback("Job", "Unknown provider requested")

    candidates = [(provider, model or DEFAULT_MODELS.get(provider, ""), api_key)]
    return await analyze_job_with_fallback(prompt_context, candidates, prompt_version)


async def analyze_job_with_fallback(
    prompt_context: str,
    candidates: list,
    prompt_version: str = CURRENT_PROMPT_VERSION,
    db=None,
    user_id=None,
) -> AnalysisOutput:
    """Run job analysis over an ordered candidate list, returning the first valid result.

    Uses Instructor-powered structured completion with candidate fallback and
    telemetry tracking. Falls back to raw text completion if structured generation
    encounters unexpected provider errors.
    """
    system_prompt = PROMPTS.get(prompt_version, PROMPTS[CURRENT_PROMPT_VERSION])
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt_context},
    ]

    try:
        from app.services.structured_ai import structured_completion_with_fallback
        from app.schemas.ai_output import AIJobAnalysisOutput
        import uuid

        user_uuid = uuid.UUID(str(user_id)) if user_id else None
        res, _ = await structured_completion_with_fallback(
            operation="job_analysis",
            response_model=AIJobAnalysisOutput,
            messages=messages,
            candidates=candidates,
            db=db,
            user_id=user_uuid,
        )
        return AnalysisOutput(
            score=res.score,
            summary=res.summary,
            pros=res.pros,
            cons=res.cons,
            skills_gap=res.skills_gap,
            key_requirements=res.key_requirements,
            seniority=res.seniority,
        )
    except Exception as structured_err:
        logger.warning(
            "Structured job analysis failed (%s); falling back to legacy completion loop",
            structured_err,
        )

    last_exc = None
    for provider, model, api_key in candidates:
        try:
            text = await _with_retry(
                lambda: complete(
                    prompt_context, api_key, provider, model=model, system=system_prompt
                ),
                max_attempts=2,
            )
            return _parse_and_validate(text)
        except Exception as exc:
            logger.warning(
                "Job analysis candidate %s/%s failed; trying next: %s",
                provider,
                model,
                exc,
            )
            last_exc = exc
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("No AI candidates were available for job analysis")


async def analyze_job_gemini(
    prompt_context: str,
    api_key: str,
    model: str = "gemini-1.5-flash",
    prompt_version: str = CURRENT_PROMPT_VERSION,
) -> AnalysisOutput:
    """Call Google Gemini and return a validated AnalysisOutput."""
    system_prompt = PROMPTS.get(prompt_version, PROMPTS[CURRENT_PROMPT_VERSION])

    async def _call():
        text = await _complete_gemini(prompt_context, api_key, model, system_prompt)
        return _parse_and_validate(text)

    return await _with_retry(_call)


async def analyze_job_anthropic(
    prompt_context: str,
    api_key: str,
    model: str = "claude-3-5-sonnet-20240620",
    prompt_version: str = CURRENT_PROMPT_VERSION,
) -> AnalysisOutput:
    """Call Anthropic and return a validated AnalysisOutput."""
    system_prompt = PROMPTS.get(prompt_version, PROMPTS[CURRENT_PROMPT_VERSION])

    async def _call():
        text = await _complete_anthropic(
            prompt_context, api_key, model, system_prompt, 1024
        )
        return _parse_and_validate(text)

    return await _with_retry(_call)


async def analyze_job_openai_compatible(
    prompt_context: str,
    api_key: str,
    base_url: str,
    model: str,
    prompt_version: str = CURRENT_PROMPT_VERSION,
    provider_name: str = "AI Provider",
) -> AnalysisOutput:
    """Call an OpenAI-compatible API and return a validated AnalysisOutput."""
    system_prompt = PROMPTS.get(prompt_version, PROMPTS[CURRENT_PROMPT_VERSION])

    async def _call():
        text = await _complete_openai_compatible(
            prompt_context, api_key, base_url, model, system_prompt, provider_name
        )
        return _parse_and_validate(text)

    return await _with_retry(_call)


async def analyze_job_openrouter(
    prompt_context: str,
    api_key: str,
    model: str = "openai/gpt-4o-mini",
    prompt_version: str = CURRENT_PROMPT_VERSION,
) -> AnalysisOutput:
    """Legacy wrapper for OpenRouter."""
    return await analyze_job_openai_compatible(
        prompt_context,
        api_key,
        base_url="https://openrouter.ai/api/v1",
        model=model,
        prompt_version=prompt_version,
        provider_name="OpenRouter",
    )


# ---------------------------------------------------------------------------
# Fallback: simple keyword scorer returning AnalysisOutput shape
# ---------------------------------------------------------------------------


def keyword_fallback(job_title: str, job_description: str) -> AnalysisOutput:
    """Produce a minimal AnalysisOutput when AI is unavailable."""
    return AnalysisOutput(
        score=0,
        summary=f"AI analysis unavailable. {job_title} at this company could not be analyzed automatically.",
        pros=["Job description imported successfully"],
        cons=["AI integration not configured — configure an API key in Settings → AI"],
        skills_gap=[],
        key_requirements=[],
        seniority="Mid",
    )
