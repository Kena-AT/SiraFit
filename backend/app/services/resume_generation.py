"""
Resume generation service.
Orchestrates AI-powered resume tailoring with validation and template rendering.
"""

import json
import logging
import asyncio
import html as _html
from typing import Optional, List
from pydantic import BaseModel, Field, ValidationError

from sqlalchemy.orm import Session
from app.models.profile import Profile
from app.models.job import Job
from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured output schema for AI resume generation
# ---------------------------------------------------------------------------

class TailoredExperience(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    period: str
    bullets: List[str] = Field(..., max_length=5)


class TailoredProject(BaseModel):
    name: str
    description: str
    url: Optional[str] = None


class TailoredEducation(BaseModel):
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    period: str


class TailoredResume(BaseModel):
    """Structured output from AI resume generation."""
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    summary: str = Field(..., max_length=2000)
    experience: List[TailoredExperience] = Field(..., max_length=10)
    projects: List[TailoredProject] = Field(..., max_length=6)
    skills: List[str] = Field(..., max_length=30)
    education: List[TailoredEducation] = Field(..., max_length=5)

    def model_post_init(self, __context):
        # Ensure lists don't exceed max
        self.experience = self.experience[:10]
        self.projects = self.projects[:6]
        self.skills = list(set(self.skills))[:30]
        self.education = self.education[:5]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

RESUME_GENERATION_PROMPT = """You are an expert resume writer and ATS optimization specialist.

Given a candidate's master profile and a specific job description, generate a tailored resume
that maximizes the candidate's chances of passing ATS screening and impressing hiring managers.

## MASTER PROFILE
{profile_data}

## TARGET JOB
{job_data}

## INSTRUCTIONS
1. Tailor the summary to align with the job's key requirements
2. Reorder and reframe experience bullets to highlight relevant accomplishments
3. Include quantifiable metrics where possible (%, $, time saved, users served)
4. Match keywords from the job description naturally
5. Keep total length to 1-2 pages (concise but comprehensive)
6. Prioritize recent and relevant experience
7. Use active voice and strong action verbs
8. For skills, include only relevant ones, ordered by relevance to the job

## OUTPUT FORMAT
Return ONLY a valid JSON object with this exact structure (no markdown, no extra text):

{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "+1234567890",
  "location": "City, State",
  "linkedin": "https://linkedin.com/in/username",
  "github": "https://github.com/username",
  "website": "https://portfolio.com",
  "summary": "2-4 sentence professional summary tailored to the role...",
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "location": "City, State",
      "period": "Jan 2020 – Present",
      "bullets": [
        "Achieved X by doing Y, resulting in Z% improvement...",
        "Led team of N engineers to deliver..."
      ]
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "description": "Built a... using X, Y, Z to achieve...",
      "url": "https://project-url.com"
    }}
  ],
  "skills": ["Python", "React", "AWS", "Kubernetes", "PostgreSQL"],
  "education": [
    {{
      "institution": "University Name",
      "degree": "Bachelor of Science",
      "field_of_study": "Computer Science",
      "period": "2016 – 2020"
    }}
  ]
}}

Rules:
- Return ONLY the JSON object, no markdown code fences, no extra text
- Ensure all required fields are present
- Experience bullets should be 1-2 sentences each, max 5 per role
- Skills list should be comma-separated in the JSON array, max 30 items
- Summary should be 2-4 sentences, compelling and tailored
- Do NOT make up experience — only use what's in the master profile
- Do NOT fabricate metrics unless they are already in the profile"""


# ---------------------------------------------------------------------------
# Profile serialization helper
# ---------------------------------------------------------------------------

def _serialize_profile(profile: Profile) -> str:
    """Convert a Profile ORM object to a text representation for the prompt."""
    parts = []
    parts.append(f"Name: {profile.first_name or ''} {profile.last_name or ''}".strip())
    parts.append(f"Headline: {profile.headline or 'N/A'}")
    parts.append(f"Summary: {profile.summary or 'N/A'}")
    parts.append(f"Location: {profile.location or 'N/A'}")
    parts.append(f"Email: {profile.email or 'N/A'}")
    parts.append(f"Phone: {profile.phone or 'N/A'}")
    parts.append(f"LinkedIn: {profile.linkedin or 'N/A'}")
    parts.append(f"GitHub: {profile.github or 'N/A'}")
    parts.append(f"Website: {profile.website or 'N/A'}")

    if profile.experiences:
        parts.append("\n## WORK EXPERIENCE")
        for exp in profile.experiences:
            parts.append(f"\nTitle: {exp.title}")
            parts.append(f"Company: {exp.company}")
            parts.append(f"Location: {exp.location or 'N/A'}")
            parts.append(f"Period: {exp.start_date} – {'Present' if exp.is_current else exp.end_date}")
            parts.append(f"Description: {exp.description or 'N/A'}")

    if profile.educations:
        parts.append("\n## EDUCATION")
        for edu in profile.educations:
            parts.append(f"\nInstitution: {edu.institution}")
            parts.append(f"Degree: {edu.degree or 'N/A'}")
            parts.append(f"Field: {edu.field_of_study or 'N/A'}")
            parts.append(f"Period: {edu.start_date} – {edu.end_date or 'N/A'}")

    if profile.skills:
        parts.append("\n## SKILLS")
        parts.append(", ".join([s.name for s in profile.skills]))

    if profile.projects:
        parts.append("\n## PROJECTS")
        for proj in profile.projects:
            parts.append(f"\nName: {proj.name}")
            parts.append(f"Description: {proj.description or 'N/A'}")
            parts.append(f"URL: {proj.url or 'N/A'}")

    if profile.certifications:
        parts.append("\n## CERTIFICATIONS")
        for cert in profile.certifications:
            parts.append(f"\nName: {cert.name}")
            parts.append(f"Issuer: {cert.issuer}")
            parts.append(f"Date: {cert.issue_date or 'N/A'}")

    return "\n".join(parts)


def _serialize_job(job: Job) -> str:
    """Convert a Job ORM object to a text representation for the prompt."""
    parts = [
        f"Title: {job.title}",
        f"Company: {job.company}",
        f"Location: {job.location or 'N/A'}",
    ]
    if job.salary_min or job.salary_max:
        salary = f"Salary: {job.currency or '$'}"
        if job.salary_min:
            salary += f"{job.salary_min:,}"
        if job.salary_min and job.salary_max:
            salary += f" – {job.currency or '$'}{job.salary_max:,}"
        elif job.salary_max:
            salary += f" up to {job.currency or '$'}{job.salary_max:,}"
        parts.append(salary)
    if job.tags:
        parts.append(f"Tags/Technologies: {', '.join(job.tags)}")
    if job.description:
        parts.append(f"\nDescription:\n{job.description[:4000]}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# AI Provider implementations
# ---------------------------------------------------------------------------

def _parse_ai_response(text: str) -> TailoredResume:
    """Parse and validate AI response into TailoredResume."""
    clean = text.strip()
    # Strip markdown code fences if present
    if clean.startswith("```"):
        clean = clean.split("```")[-2] if "```" in clean[3:] else clean[3:]
        if clean.lower().startswith("json"):
            clean = clean[4:]
        clean = clean.strip()
    data = json.loads(clean)
    return TailoredResume.model_validate(data)


async def _generate_with_gemini(prompt: str, api_key: str, model: str = "gemini-1.5-flash") -> TailoredResume:
    """Generate resume using Google Gemini."""
    import google.generativeai as genai

    model_name = "models/gemini-1.5-pro" if "pro" in model.lower() else "models/gemini-1.5-flash"

    genai.configure(api_key=api_key)
    gen_model = genai.GenerativeModel(model_name)
    response = gen_model.generate_content(prompt)
    return _parse_ai_response(response.text)


async def _generate_with_openrouter(prompt: str, api_key: str, model: str = "openai/gpt-4o-mini") -> TailoredResume:
    """Generate resume using OpenRouter."""
    import httpx

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert resume writer. Return only valid JSON."},
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
    text = data["choices"][0]["message"]["content"]
    return _parse_ai_response(text)


# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------

async def _with_retry(fn, max_attempts: int = 3):
    """Call async fn up to max_attempts with exponential backoff."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return await fn()
        except (json.JSONDecodeError, ValidationError) as e:
            last_exc = e
            logger.warning(f"Resume generation parse error attempt {attempt + 1}: {e}")
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)
        except Exception as e:
            last_exc = e
            logger.warning(f"Resume generation error attempt {attempt + 1}: {e}")
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)
    raise last_exc


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _calculate_ats_score(resume_data: dict, job: Job) -> int:
    """Calculate a basic ATS readiness score."""
    score = 0

    # 1. Has summary (20 pts)
    if resume_data.get("summary"):
        score += 20

    # 2. Has experience with bullets (20 pts)
    if resume_data.get("experience") and any(exp.get("bullets") for exp in resume_data["experience"]):
        score += 20

    # 3. Has skills (20 pts)
    if resume_data.get("skills") and len(resume_data["skills"]) >= 5:
        score += 20

    # 4. Keyword match with job (20 pts)
    if job.description and resume_data.get("skills"):
        job_text = f"{job.title} {job.description}".lower()
        matched = sum(1 for skill in resume_data["skills"] if skill.lower() in job_text)
        if matched >= 3:
            score += 20
        elif matched >= 1:
            score += 10

    # 5. Has education (20 pts)
    if resume_data.get("education"):
        score += 20

    return score


def validate_resume_json(resume_data: dict, job: Job) -> tuple[bool, list[str]]:
    """
    Validate a generated resume JSON structure.
    Returns (is_valid, list_of_issues).
    """
    issues = []

    required_fields = ["name", "email", "summary", "experience", "skills", "education"]
    for field in required_fields:
        if not resume_data.get(field):
            issues.append(f"Missing required field: {field}")

    if resume_data.get("experience"):
        for i, exp in enumerate(resume_data["experience"]):
            if "bullets" not in exp:
                issues.append(f"Experience {i+1} missing bullets field")
            elif exp.get("bullets") is None:
                issues.append(f"Experience {i+1} missing bullets")
            elif len(exp["bullets"]) > 5:
                issues.append(f"Experience {i+1} has more than 5 bullets")

    if not resume_data.get("skills") or len(resume_data["skills"]) == 0:
        issues.append("No skills listed")
    elif len(resume_data["skills"]) > 30:
        issues.append(f"Too many skills ({len(resume_data['skills'])}, max 30)")

    ats_score = _calculate_ats_score(resume_data, job)
    if ats_score < 60:
        issues.append(f"Low ATS score: {ats_score}/100")

    return len(issues) == 0, issues


# ---------------------------------------------------------------------------
# Template Engine
# ---------------------------------------------------------------------------

def _esc(value) -> str:
    """Escape HTML special characters in a value."""
    if value is None:
        return ""
    return _html.escape(str(value), quote=True)


TEMPLATES = {
    "minimal": {
        "name": "Minimal",
        "description": "Clean, no-frills layout optimized for ATS parsing",
    },
    "technical": {
        "name": "Technical",
        "description": "Projects and skills forward, ideal for engineering roles",
    },
    "modern": {
        "name": "Modern",
        "description": "Balanced layout with subtle styling",
    },
    "corporate": {
        "name": "Corporate",
        "description": "Traditional layout for conservative industries",
    },
    "compact": {
        "name": "Compact",
        "description": "Fits maximum content in minimal space",
    },
}


def render_resume_html(resume_data: dict, template: str = "minimal") -> str:
    """
    Render a resume JSON into HTML using the specified template.
    Returns the HTML string.
    """
    template_name = template if template in TEMPLATES else "minimal"

    if template_name == "minimal":
        return _render_minimal_template(resume_data)
    if template_name == "technical":
        return _render_technical_template(resume_data)
    if template_name == "modern":
        return _render_modern_template(resume_data)
    if template_name == "corporate":
        return _render_corporate_template(resume_data)
    if template_name == "compact":
        return _render_compact_template(resume_data)
    return _render_minimal_template(resume_data)


def _render_minimal_template(resume_data: dict) -> str:
    """Render the minimal template."""
    name = _esc(resume_data.get("name", ""))
    email = _esc(resume_data.get("email", ""))
    phone = _esc(resume_data.get("phone", ""))
    location = _esc(resume_data.get("location", ""))
    linkedin = _esc(resume_data.get("linkedin", ""))
    github = _esc(resume_data.get("github", ""))
    website = _esc(resume_data.get("website", ""))

    lines = []
    lines.append("<!DOCTYPE html>")
    lines.append("<html><head><meta charset='utf-8'><style>")
    lines.append("body{font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:40px;line-height:1.6}")
    lines.append("h1{font-size:24px;margin-bottom:4px}")
    lines.append(".contact{font-size:13px;color:#666;margin-bottom:20px}")
    lines.append("h2{font-size:16px;border-bottom:1px solid #ccc;padding-bottom:4px;margin-top:20px;margin-bottom:10px}")
    lines.append(".exp-item{margin-bottom:16px}")
    lines.append(".exp-header{display:flex;justify-content:space-between;font-weight:bold}")
    lines.append(".exp-meta{color:#666;font-size:13px}")
    lines.append("ul{margin:4px 0;padding-left:20px}")
    lines.append("li{margin:2px 0;font-size:14px}")
    lines.append(".skills{font-size:14px}")
    lines.append("</style></head><body>")

    # Header
    lines.append(f"<h1>{name}</h1>")
    contact_parts = []
    if email:
        contact_parts.append(email)
    if phone:
        contact_parts.append(phone)
    if location:
        contact_parts.append(location)
    if linkedin:
        contact_parts.append(linkedin)
    if github:
        contact_parts.append(github)
    if website:
        contact_parts.append(website)
    lines.append(f"<div class='contact'>{' · '.join(contact_parts)}</div>")

    # Summary
    if resume_data.get("summary"):
        lines.append("<h2>Summary</h2>")
        lines.append(f"<p>{_esc(resume_data['summary'])}</p>")

    # Experience
    if resume_data.get("experience"):
        lines.append("<h2>Experience</h2>")
        for exp in resume_data["experience"]:
            title = _esc(exp.get("title", ""))
            company = _esc(exp.get("company", ""))
            period = _esc(exp.get("period", ""))
            loc = _esc(exp.get("location", ""))
            lines.append("<div class='exp-item'>")
            lines.append(f"<div class='exp-header'><span>{title} — {company}</span><span>{period}</span></div>")
            if loc:
                lines.append(f"<div class='exp-meta'>{loc}</div>")
            if exp.get("bullets"):
                lines.append("<ul>")
                for bullet in exp["bullets"]:
                    lines.append(f"<li>{_esc(bullet)}</li>")
                lines.append("</ul>")
            lines.append("</div>")

    # Projects
    if resume_data.get("projects"):
        lines.append("<h2>Projects</h2>")
        for proj in resume_data["projects"]:
            pname = _esc(proj.get("name", ""))
            pdesc = _esc(proj.get("description", ""))
            lines.append(f"<p><strong>{pname}</strong> — {pdesc}</p>")

    # Skills
    if resume_data.get("skills"):
        lines.append("<h2>Skills</h2>")
        escaped_skills = [_esc(s) for s in resume_data["skills"]]
        lines.append(f"<p class='skills'>{' · '.join(escaped_skills)}</p>")

    # Education
    if resume_data.get("education"):
        lines.append("<h2>Education</h2>")
        for edu in resume_data["education"]:
            inst = _esc(edu.get("institution", ""))
            deg = _esc(edu.get("degree", ""))
            field = _esc(edu.get("field_of_study", ""))
            period = _esc(edu.get("period", ""))
            lines.append(f"<p><strong>{inst}</strong> — {deg}, {field} ({period})</p>")

    lines.append("</body></html>")
    return "\n".join(lines)


def _render_technical_template(resume_data: dict) -> str:
    """Render the technical template (skills and projects forward)."""
    name = _esc(resume_data.get("name", ""))
    email = _esc(resume_data.get("email", ""))
    phone = _esc(resume_data.get("phone", ""))
    location = _esc(resume_data.get("location", ""))
    linkedin = _esc(resume_data.get("linkedin", ""))
    github = _esc(resume_data.get("github", ""))

    lines = []
    lines.append("<!DOCTYPE html>")
    lines.append("<html><head><meta charset='utf-8'><style>")
    lines.append("body{font-family:'Segoe UI',Arial,sans-serif;max-width:800px;margin:0 auto;padding:40px;line-height:1.6}")
    lines.append("h1{font-size:26px;margin-bottom:4px;color:#1a1a1a}")
    lines.append(".contact{font-size:13px;color:#555;margin-bottom:24px}")
    lines.append("h2{font-size:15px;text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid #2563eb;padding-bottom:6px;margin-top:24px;margin-bottom:12px;color:#1e40af}")
    lines.append(".exp-item{margin-bottom:18px}")
    lines.append(".exp-header{display:flex;justify-content:space-between;font-weight:600}")
    lines.append(".exp-meta{color:#666;font-size:13px}")
    lines.append("ul{margin:6px 0;padding-left:20px}")
    lines.append("li{margin:3px 0;font-size:14px}")
    lines.append(".skills{display:flex;flex-wrap:wrap;gap:6px}")
    lines.append(".skill-tag{background:#eff6ff;color:#1e40af;padding:3px 8px;border-radius:4px;font-size:13px}")
    lines.append("</style></head><body>")

    # Header
    lines.append(f"<h1>{name}</h1>")
    contact_parts = []
    if email:
        contact_parts.append(email)
    if phone:
        contact_parts.append(phone)
    if location:
        contact_parts.append(location)
    if linkedin:
        contact_parts.append(linkedin)
    if github:
        contact_parts.append(github)
    lines.append(f"<div class='contact'>{' · '.join(contact_parts)}</div>")

    # Summary
    if resume_data.get("summary"):
        lines.append("<h2>Summary</h2>")
        lines.append(f"<p>{_esc(resume_data['summary'])}</p>")

    # Skills (forward for technical roles)
    if resume_data.get("skills"):
        lines.append("<h2>Technical Skills</h2>")
        lines.append("<div class='skills'>")
        for skill in resume_data["skills"]:
            lines.append(f"<span class='skill-tag'>{_esc(skill)}</span>")
        lines.append("</div>")

    # Projects
    if resume_data.get("projects"):
        lines.append("<h2>Projects</h2>")
        for proj in resume_data["projects"]:
            pname = _esc(proj.get("name", ""))
            pdesc = _esc(proj.get("description", ""))
            purl = _esc(proj.get("url", "") or "")
            lines.append(f"<p><strong>{pname}</strong></p>")
            lines.append(f"<p>{pdesc}</p>")
            if purl:
                lines.append(f"<p><a href='{purl}'>{purl}</a></p>")

    # Experience
    if resume_data.get("experience"):
        lines.append("<h2>Experience</h2>")
        for exp in resume_data["experience"]:
            title = _esc(exp.get("title", ""))
            company = _esc(exp.get("company", ""))
            period = _esc(exp.get("period", ""))
            loc = _esc(exp.get("location", ""))
            lines.append("<div class='exp-item'>")
            lines.append(f"<div class='exp-header'><span>{title} — {company}</span><span>{period}</span></div>")
            if loc:
                lines.append(f"<div class='exp-meta'>{loc}</div>")
            if exp.get("bullets"):
                lines.append("<ul>")
                for bullet in exp["bullets"]:
                    lines.append(f"<li>{_esc(bullet)}</li>")
                lines.append("</ul>")
            lines.append("</div>")

    # Education
    if resume_data.get("education"):
        lines.append("<h2>Education</h2>")
        for edu in resume_data["education"]:
            inst = _esc(edu.get("institution", ""))
            deg = _esc(edu.get("degree", ""))
            field = _esc(edu.get("field_of_study", ""))
            period = _esc(edu.get("period", ""))
            lines.append(f"<p><strong>{inst}</strong> — {deg}, {field} ({period})</p>")

    lines.append("</body></html>")
    return "\n".join(lines)

def _render_modern_template(resume_data: dict) -> str:
    """Render the modern template: balanced layout with subtle styling and a sidebar accent."""
    name = _esc(resume_data.get("name", ""))
    email = _esc(resume_data.get("email", ""))
    phone = _esc(resume_data.get("phone", ""))
    location = _esc(resume_data.get("location", ""))
    linkedin = _esc(resume_data.get("linkedin", ""))
    github = _esc(resume_data.get("github", ""))
    website = _esc(resume_data.get("website", ""))

    contact = " · ".join([c for c in [email, phone, location] if c])
    links = " · ".join([link for link in [linkedin, github, website] if link])

    lines = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'><style>",
        "body{font-family:'Segoe UI',Arial,sans-serif;max-width:840px;margin:0 auto;padding:0;line-height:1.6;color:#1f2937}",
        ".header{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;padding:36px 40px}",
        ".header h1{font-size:28px;margin:0 0 6px 0;letter-spacing:-0.5px}",
        ".header .contact{font-size:13px;opacity:.9}",
        ".header .links{font-size:12px;opacity:.85;margin-top:4px}",
        ".body{padding:28px 40px}",
        "h2{font-size:14px;text-transform:uppercase;letter-spacing:1.5px;color:#6366f1;border-bottom:1px solid #e5e7eb;padding-bottom:6px;margin:24px 0 12px}",
        ".exp-item{margin-bottom:16px}",
        ".exp-header{display:flex;justify-content:space-between;font-weight:600;font-size:15px}",
        ".exp-meta{color:#6b7280;font-size:12px}",
        "ul{margin:6px 0;padding-left:20px}",
        "li{margin:3px 0;font-size:13px}",
        ".skills-grid{display:flex;flex-wrap:wrap;gap:6px}",
        ".skill{background:#eef2ff;color:#4338ca;padding:4px 10px;border-radius:999px;font-size:12px}",
        ".project{margin-bottom:10px}",
        ".project a{color:#6366f1;text-decoration:none}",
        ".edu{display:flex;justify-content:space-between;font-size:13px}",
        "</style></head><body>",
        f"<div class='header'><h1>{name}</h1>",
        f"<div class='contact'>{contact}</div>",
        f"<div class='links'>{links}</div></div>",
        "<div class='body'>",
    ]

    if resume_data.get("summary"):
        lines.append(f"<h2>About</h2><p>{_esc(resume_data['summary'])}</p>")

    if resume_data.get("experience"):
        lines.append("<h2>Experience</h2>")
        for exp in resume_data["experience"]:
            title = _esc(exp.get("title", ""))
            company = _esc(exp.get("company", ""))
            period = _esc(exp.get("period", ""))
            loc = _esc(exp.get("location", ""))
            lines.append("<div class='exp-item'>")
            lines.append(f"<div class='exp-header'><span>{title} · {company}</span><span>{period}</span></div>")
            if loc:
                lines.append(f"<div class='exp-meta'>{loc}</div>")
            if exp.get("bullets"):
                lines.append("<ul>")
                for b in exp["bullets"]:
                    lines.append(f"<li>{_esc(b)}</li>")
                lines.append("</ul>")
            lines.append("</div>")

    if resume_data.get("skills"):
        lines.append("<h2>Skills</h2><div class='skills-grid'>")
        for s in resume_data["skills"]:
            lines.append(f"<span class='skill'>{_esc(s)}</span>")
        lines.append("</div>")

    if resume_data.get("projects"):
        lines.append("<h2>Projects</h2>")
        for p in resume_data["projects"]:
            pname = _esc(p.get("name", ""))
            pdesc = _esc(p.get("description", ""))
            purl = _esc(p.get("url", "") or "")
            lines.append(f"<div class='project'><strong>{pname}</strong> — {pdesc}")
            if purl:
                lines.append(f" <a href='{purl}'>{purl}</a>")
            lines.append("</div>")

    if resume_data.get("education"):
        lines.append("<h2>Education</h2>")
        for edu in resume_data["education"]:
            inst = _esc(edu.get("institution", ""))
            deg = _esc(edu.get("degree", ""))
            field = _esc(edu.get("field_of_study", ""))
            period = _esc(edu.get("period", ""))
            lines.append(f"<div class='edu'><span><strong>{inst}</strong> — {deg}, {field}</span><span>{period}</span></div>")

    lines.append("</div></body></html>")
    return "\n".join(lines)


def _render_corporate_template(resume_data: dict) -> str:
    """Render the corporate template: traditional layout for conservative industries."""
    name = _esc(resume_data.get("name", ""))
    email = _esc(resume_data.get("email", ""))
    phone = _esc(resume_data.get("phone", ""))
    location = _esc(resume_data.get("location", ""))
    linkedin = _esc(resume_data.get("linkedin", ""))
    github = _esc(resume_data.get("github", ""))
    website = _esc(resume_data.get("website", ""))

    contact = " | ".join([c for c in [email, phone, location] if c])
    links = " | ".join([link for link in [linkedin, github, website] if link])

    lines = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'><style>",
        "body{font-family:'Times New Roman',Georgia,serif;max-width:800px;margin:0 auto;padding:40px;line-height:1.5;color:#000}",
        ".name{text-align:center;font-size:26px;font-variant:small-caps;letter-spacing:2px;border-bottom:2px solid #000;padding-bottom:8px;margin-bottom:4px}",
        ".contact{text-align:center;font-size:12px;color:#333;margin-bottom:6px}",
        ".links{text-align:center;font-size:11px;color:#555;margin-bottom:24px}",
        "h2{font-size:14px;font-variant:small-caps;letter-spacing:2px;border-bottom:1px solid #000;padding-bottom:3px;margin:22px 0 10px}",
        ".exp-item{margin-bottom:14px}",
        ".exp-header{font-weight:bold;font-size:14px}",
        ".exp-sub{font-style:italic;font-size:12px;color:#444;margin:1px 0 4px}",
        "ul{margin:4px 0;padding-left:22px}",
        "li{margin:2px 0;font-size:13px;text-align:justify}",
        ".skills{font-size:13px}",
        ".project{margin-bottom:8px}",
        ".edu-item{margin-bottom:6px;font-size:13px}",
        "</style></head><body>",
        f"<div class='name'>{name}</div>",
        f"<div class='contact'>{contact}</div>",
        f"<div class='links'>{links}</div>",
    ]

    if resume_data.get("summary"):
        lines.append(f"<h2>Professional Summary</h2><p style='font-size:13px;text-align:justify'>{_esc(resume_data['summary'])}</p>")

    if resume_data.get("experience"):
        lines.append("<h2>Professional Experience</h2>")
        for exp in resume_data["experience"]:
            title = _esc(exp.get("title", ""))
            company = _esc(exp.get("company", ""))
            period = _esc(exp.get("period", ""))
            loc = _esc(exp.get("location", ""))
            lines.append("<div class='exp-item'>")
            lines.append(f"<div class='exp-header'>{title}, {company}</div>")
            sub = period
            if loc:
                sub = f"{loc} — {period}"
            lines.append(f"<div class='exp-sub'>{sub}</div>")
            if exp.get("bullets"):
                lines.append("<ul>")
                for b in exp["bullets"]:
                    lines.append(f"<li>{_esc(b)}</li>")
                lines.append("</ul>")
            lines.append("</div>")

    if resume_data.get("education"):
        lines.append("<h2>Education</h2>")
        for edu in resume_data["education"]:
            inst = _esc(edu.get("institution", ""))
            deg = _esc(edu.get("degree", ""))
            field = _esc(edu.get("field_of_study", ""))
            period = _esc(edu.get("period", ""))
            line = f"<div class='edu-item'><strong>{inst}</strong>"
            if deg:
                line += f" — {deg}"
            if field:
                line += f", {field}"
            line += f" ({period})</div>"
            lines.append(line)

    if resume_data.get("skills"):
        lines.append("<h2>Technical Skills</h2>")
        lines.append(f"<p class='skills'>{_esc(', '.join(resume_data['skills']))}</p>")

    if resume_data.get("projects"):
        lines.append("<h2>Selected Projects</h2>")
        for p in resume_data["projects"]:
            pname = _esc(p.get("name", ""))
            pdesc = _esc(p.get("description", ""))
            purl = _esc(p.get("url", "") or "")
            line = f"<div class='project'><strong>{pname}.</strong> {pdesc}"
            if purl:
                line += f" <em>{purl}</em>"
            line += "</div>"
            lines.append(line)

    lines.append("</body></html>")
    return "\n".join(lines)


def _render_compact_template(resume_data: dict) -> str:
    """Render the compact template: maximizes content density in minimal space."""
    name = _esc(resume_data.get("name", ""))
    email = _esc(resume_data.get("email", ""))
    phone = _esc(resume_data.get("phone", ""))
    location = _esc(resume_data.get("location", ""))
    linkedin = _esc(resume_data.get("linkedin", ""))
    github = _esc(resume_data.get("github", ""))
    website = _esc(resume_data.get("website", ""))

    contact = " · ".join([c for c in [email, phone, location, linkedin, github, website] if c])

    lines = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'><style>",
        "body{font-family:Arial,sans-serif;max-width:780px;margin:0 auto;padding:24px;line-height:1.35;color:#111;font-size:12px}",
        ".header{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1.5px solid #111;padding-bottom:6px;margin-bottom:10px}",
        ".header h1{font-size:20px;margin:0;letter-spacing:-0.3px}",
        ".header .contact{font-size:10px;color:#555;text-align:right;max-width:50%}",
        "h2{font-size:11px;text-transform:uppercase;letter-spacing:1px;border-bottom:0.5px solid #ccc;margin:14px 0 6px;padding-bottom:2px}",
        ".exp-item{margin-bottom:8px}",
        ".exp-line{display:flex;justify-content:space-between;font-weight:600;font-size:12px}",
        ".exp-meta{color:#666;font-size:10px}",
        "ul{margin:2px 0;padding-left:16px}",
        "li{margin:0;font-size:11px}",
        ".skills{font-size:11px}",
        ".project{font-size:11px;margin-bottom:4px}",
        ".edu-line{display:flex;justify-content:space-between;font-size:11px}",
        "</style></head><body>",
        f"<div class='header'><h1>{name}</h1><div class='contact'>{contact}</div></div>",
    ]

    if resume_data.get("summary"):
        lines.append(f"<h2>Summary</h2><p style='font-size:11px;margin:2px 0'>{_esc(resume_data['summary'])}</p>")

    if resume_data.get("experience"):
        lines.append("<h2>Experience</h2>")
        for exp in resume_data["experience"]:
            title = _esc(exp.get("title", ""))
            company = _esc(exp.get("company", ""))
            period = _esc(exp.get("period", ""))
            loc = _esc(exp.get("location", ""))
            lines.append("<div class='exp-item'>")
            lines.append(f"<div class='exp-line'><span>{title} · {company}</span><span>{period}</span></div>")
            if loc:
                lines.append(f"<div class='exp-meta'>{loc}</div>")
            if exp.get("bullets"):
                lines.append("<ul>")
                for b in exp["bullets"]:
                    lines.append(f"<li>{_esc(b)}</li>")
                lines.append("</ul>")
            lines.append("</div>")

    if resume_data.get("skills"):
        lines.append("<h2>Skills</h2>")
        lines.append(f"<p class='skills'>{_esc(' · '.join(resume_data['skills']))}</p>")

    if resume_data.get("projects"):
        lines.append("<h2>Projects</h2>")
        for p in resume_data["projects"]:
            pname = _esc(p.get("name", ""))
            pdesc = _esc(p.get("description", ""))
            purl = _esc(p.get("url", "") or "")
            line = f"<div class='project'><strong>{pname}</strong> — {pdesc}"
            if purl:
                line += f" <span style='color:#666'>({purl})</span>"
            line += "</div>"
            lines.append(line)

    if resume_data.get("education"):
        lines.append("<h2>Education</h2>")
        for edu in resume_data["education"]:
            inst = _esc(edu.get("institution", ""))
            deg = _esc(edu.get("degree", ""))
            field = _esc(edu.get("field_of_study", ""))
            period = _esc(edu.get("period", ""))
            left = inst
            if deg:
                left += f" — {deg}"
            if field:
                left += f", {field}"
            lines.append(f"<div class='edu-line'><span>{left}</span><span>{period}</span></div>")
    lines.append("</body></html>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main generation orchestrator
# ---------------------------------------------------------------------------

async def generate_tailored_resume(
    db: Session,
    user_id: str,
    profile: Profile,
    job: Job,
    template: str = "minimal",
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    """
    Generate a tailored resume for a specific job.

    Args:
        db: Database session
        user_id: User ID (string)
        profile: User's master profile
        job: Target job
        template: Template name (minimal, technical, modern, corporate, compact)
        api_key: Optional API key override
        provider: AI provider (gemini, openrouter)
        model: Model name

    Returns:
        dict with keys: resume_data (TailoredResume), html (str), ats_score (int), issues (list)
    """

    # Build prompt context
    profile_text = _serialize_profile(profile)
    job_text = _serialize_job(job)
    prompt = RESUME_GENERATION_PROMPT.format(profile_data=profile_text, job_data=job_text)

    # Determine provider and key
    actual_provider = (provider or "").lower()
    actual_model = model or ""
    actual_key = api_key

    if not actual_key:
        if actual_provider == "openrouter":
            actual_key = getattr(settings, 'OPENROUTER_API_KEY', None)
        else:
            actual_key = getattr(settings, 'GEMINI_API_KEY', None)
            actual_provider = "gemini" if not actual_provider else actual_provider

    # Generate resume data
    if actual_key and actual_provider == "gemini":
        tailored = await _with_retry(lambda: _generate_with_gemini(prompt, actual_key, actual_model or "gemini-1.5-flash"))
    elif actual_key and actual_provider == "openrouter":
        tailored = await _with_retry(lambda: _generate_with_openrouter(prompt, actual_key, actual_model or "openai/gpt-4o-mini"))
    else:
        raise ValueError("No AI API key configured for resume generation")

    resume_data = tailored.model_dump()

    # Validate
    is_valid, issues = validate_resume_json(resume_data, job)

    # Calculate ATS score
    ats_score = _calculate_ats_score(resume_data, job)

    # Render HTML
    html = render_resume_html(resume_data, template)

    return {
        "resume_data": resume_data,
        "html": html,
        "ats_score": ats_score,
        "issues": issues,
        "is_valid": is_valid,
    }