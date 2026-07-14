"""
Cover letter generation service.

Orchestrates AI-powered cover letter writing from a candidate's profile
and a target job.  Returns structured text + rendered HTML.
"""

import logging
import asyncio
import html as _html_lib
from typing import Optional

from app.core.config import settings
from app.models.profile import Profile
from app.models.job import Job

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

COVER_LETTER_PROMPT = """You are an expert career coach and cover letter writer.

Given a candidate's profile and a job description, write a compelling,
concise, and personalized cover letter. The letter should:

1. Open with a strong hook that shows genuine interest in the company/role
2. Connect 2–3 specific experiences or skills from the profile to the job requirements
3. Use concrete metrics and outcomes where possible
4. Stay under 300 words (concise is key)
5. Match the tone specified by the user
   (matching = mirror the job's tone, conversational = warm and friendly, formal = traditional)
6. Close with a confident call to action

## CANDIDATE PROFILE
{profile_data}

## TARGET JOB
{job_data}

## TONE
{tone}

## INSTRUCTIONS
- Write ONLY the cover letter body (no headers, no CSS, no meta text)
- Use a professional greeting like "Dear Hiring Manager," or "Dear [Team] Team,""
- Sign off with the candidate's name
- Keep to 3–4 short paragraphs
- Be specific about why THIS role at THIS company

Return ONLY plain text (no markdown, no code fences)."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize_profile(profile: Profile) -> str:
    """Convert a Profile ORM object to a text representation."""
    parts = [
        f"Name: {profile.first_name or ''} {profile.last_name or ''}".strip(),
        f"Headline: {profile.headline or 'N/A'}",
        f"Summary: {profile.summary or 'N/A'}",
    ]
    if profile.experiences:
        parts.append("\n## WORK EXPERIENCE")
        for exp in profile.experiences:
            parts.append(f"\n{exp.title} at {exp.company}")
            parts.append(f"  {exp.description or 'N/A'}")
    if profile.skills:
        parts.append(f"\n## SKILLS\n{', '.join([s.name for s in profile.skills])}")
    return "\n".join(parts)


def _serialize_job(job: Job) -> str:
    """Convert a Job ORM object to a text representation."""
    parts = [
        f"Title: {job.title}",
        f"Company: {job.company}",
        f"Location: {job.location or 'N/A'}",
    ]
    if job.description:
        parts.append(f"\n{job.description[:2000]}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# AI providers (mirrors resume_generation.py)
# ---------------------------------------------------------------------------


async def _generate_with_gemini(
    prompt: str, api_key: str, model: str = "gemini-1.5-flash"
) -> str:
    """Generate cover letter using Google Gemini."""
    import google.generativeai as genai

    model_name = (
        "models/gemini-1.5-pro" if "pro" in model.lower() else "models/gemini-1.5-flash"
    )
    genai.configure(api_key=api_key)
    gen_model = genai.GenerativeModel(model_name)
    response = gen_model.generate_content(prompt)
    return response.text.strip()


async def _generate_with_openrouter(
    prompt: str, api_key: str, model: str = "openai/gpt-4o-mini"
) -> str:
    """Generate cover letter using OpenRouter."""
    import httpx

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert cover letter writer. Return only plain text.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://sirafit.com",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    return data["choices"][0]["message"]["content"].strip()


async def _with_retry(fn, max_attempts: int = 3):
    """Call async fn up to max_attempts with exponential backoff."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return await fn()
        except Exception as e:
            last_exc = e
            logger.warning(f"Cover letter generation error attempt {attempt + 1}: {e}")
            if attempt < max_attempts - 1:
                await asyncio.sleep(2**attempt)
    raise last_exc


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------


async def generate_cover_letter(
    profile: Profile,
    job: Job,
    tone: str = "matching",
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
) -> str:
    """
    Generate a tailored cover letter.

    Args:
        profile: User's master profile
        job: Target job
        tone: "matching", "conversational", or "formal"
        api_key: Optional API key override
        provider: "gemini" or "openrouter"

    Returns:
        Plain text cover letter body
    """
    profile_text = _serialize_profile(profile)
    job_text = _serialize_job(job)
    prompt = COVER_LETTER_PROMPT.format(
        profile_data=profile_text,
        job_data=job_text,
        tone=tone,
    )

    actual_provider = (provider or "").lower()
    actual_model = ""
    actual_key = api_key

    if not actual_key:
        if actual_provider == "openrouter":
            actual_key = getattr(settings, "OPENROUTER_API_KEY", None)
        else:
            actual_key = getattr(settings, "GEMINI_API_KEY", None)
            actual_provider = "gemini" if not actual_provider else actual_provider

    if actual_key and actual_provider == "gemini":
        body = await _with_retry(
            lambda: _generate_with_gemini(
                prompt, actual_key, actual_model or "gemini-1.5-flash"
            ),
        )
    elif actual_key and actual_provider == "openrouter":
        body = await _with_retry(
            lambda: _generate_with_openrouter(
                prompt, actual_key, actual_model or "openai/gpt-4o-mini"
            ),
        )
    else:
        raise ValueError("No AI API key configured for cover letter generation")

    return body


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------


def render_cover_letter_html(body: str, template: str = "classic") -> str:
    """Render a cover letter body into HTML using the specified template."""
    template_name = (
        template if template in ("classic", "modern", "compact") else "classic"
    )
    if template_name == "classic":
        return _render_classic(body)
    if template_name == "modern":
        return _render_modern(body)
    return _render_compact(body)


def _render_classic(body: str) -> str:
    if not body.strip():
        return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{font-family:Georgia,serif;max-width:600px;margin:40px auto;line-height:1.7;color:#333}
</style></head><body></body></html>"""
    lines = body.splitlines()
    html_lines = ["<p>" + _esc(lines[0]) + "</p>"]
    current_paragraph = []
    for line in lines[1:]:
        if not line.strip():
            if current_paragraph:
                html_lines.append("<p>" + "".join(current_paragraph) + "</p>")
                current_paragraph = []
        else:
            current_paragraph.append(_esc(line))
    if current_paragraph:
        html_lines.append("<p>" + "".join(current_paragraph) + "</p>")

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{font-family:Georgia,serif;max-width:600px;margin:40px auto;line-height:1.7;color:#333}}
p{{margin:1em 0;text-indent:2em}}
</style></head><body>{"".join(html_lines)}</body></html>"""


def _render_modern(body: str) -> str:
    paragraphs = body.split("\n\n")
    html_paragraphs = ""
    for p in paragraphs:
        if p.strip():
            html_paragraphs += (
                f'<p style="margin:1.2em 0;font-size:15px;color:#1f2937">{_esc(p)}</p>'
            )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:40px auto;line-height:1.7;color:#1f2937}}
</style></head><body>{html_paragraphs}</body></html>"""


def _render_compact(body: str) -> str:
    paragraphs = body.split("\n\n")
    html_paragraphs = ""
    for p in paragraphs:
        if p.strip():
            html_paragraphs += (
                f'<p style="margin:0.4em 0;font-size:12px;color:#111">{_esc(p)}</p>'
            )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{font-family:Arial,sans-serif;max-width:640px;margin:20px auto;line-height:1.35;color:#111;font-size:12px}}
</style></head><body>{html_paragraphs}</body></html>"""


def _esc(value: str) -> str:
    if not value:
        return ""
    return _html_lib.escape(value, quote=True)
