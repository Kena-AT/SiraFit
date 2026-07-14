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

async def _with_retry(fn, max_attempts: int = 3):
    """Call async fn up to max_attempts times with exponential backoff."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return await fn()
        except (json.JSONDecodeError, ValidationError, KeyError) as e:
            last_exc = e
            logger.warning(f"AI parse/validation error attempt {attempt + 1}: {e}")
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
        except Exception as e:
            last_exc = e
            logger.warning(f"AI call error attempt {attempt + 1}: {e}")
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)
    raise last_exc


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

async def analyze_job_gemini(
    prompt_context: str,
    api_key: str,
    model: str = "gemini-1.5-flash",
    prompt_version: str = CURRENT_PROMPT_VERSION,
) -> AnalysisOutput:
    """Call Google Gemini and return a validated AnalysisOutput."""
    import google.generativeai as genai

    system_prompt = PROMPTS.get(prompt_version, PROMPTS[CURRENT_PROMPT_VERSION])
    full_prompt = f"{system_prompt}\n\n{prompt_context}"

    model_name = "models/gemini-1.5-pro" if "pro" in model.lower() else "models/gemini-1.5-flash"

    async def _call():
        genai.configure(api_key=api_key)
        gen_model = genai.GenerativeModel(model_name)
        response = gen_model.generate_content(full_prompt)
        return _parse_and_validate(response.text)

    return await _with_retry(_call)


async def analyze_job_openrouter(
    prompt_context: str,
    api_key: str,
    model: str = "openai/gpt-4o-mini",
    prompt_version: str = CURRENT_PROMPT_VERSION,
) -> AnalysisOutput:
    """Call OpenRouter and return a validated AnalysisOutput."""
    system_prompt = PROMPTS.get(prompt_version, PROMPTS[CURRENT_PROMPT_VERSION])

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_context},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://sirafit.com",
        "Content-Type": "application/json",
    }

    async def _call():
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        text = data["choices"][0]["message"]["content"]
        return _parse_and_validate(text)

    return await _with_retry(_call)


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
