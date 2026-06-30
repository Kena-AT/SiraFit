import re
from typing import Tuple
from app.models.profile import Profile
from app.models.job import Job
from app.core.config import settings
from app.services.ai import analyze_job_match_gemini, analyze_job_match_openrouter

async def analyze_match_score(profile: Profile, job: Job, req_api_key: str = None, provider: str = None, model: str = None) -> Tuple[int, str]:
    if not profile or not job:
        return 0, "Missing profile or job data."

    # Determine provider and key
    actual_provider = (provider or "").lower()
    actual_model = model or ""
    actual_key = req_api_key

    if not actual_key:
        if actual_provider == "openrouter":
            actual_key = settings.OPENROUTER_API_KEY
        else:
            actual_key = settings.GEMINI_API_KEY
            actual_provider = "gemini" if not actual_provider else actual_provider

    if actual_key and actual_provider == "gemini":
        return await analyze_job_match_gemini(profile, job, actual_key, actual_model)
    elif actual_key and actual_provider == "openrouter":
        return await analyze_job_match_openrouter(profile, job, actual_key, actual_model)
    
    # Fallback to existing keyword matcher
    return _keyword_match_score(profile, job)

def _keyword_match_score(profile: Profile, job: Job) -> Tuple[int, str]:
    score = 0
    reasons = []

    job_text = f"{job.title} {job.description or ''} {' '.join(job.tags or [])}".lower()
    
    matched_skills = []
    if profile.skills:
        for skill in profile.skills:
            if skill.name.lower() in job_text:
                matched_skills.append(skill.name)
        
        skill_score = min(50, len(matched_skills) * 10)
        score += skill_score
        if matched_skills:
            reasons.append(f"Matched skills: {', '.join(matched_skills)}.")
        else:
            reasons.append("No matching skills found.")
    else:
        reasons.append("Profile has no skills listed.")

    exp_matched = False
    if profile.experiences:
        for exp in profile.experiences:
            if any(word in exp.title.lower() for word in job.title.lower().split()):
                exp_matched = True
                break
        
        if exp_matched:
            score += 30
            reasons.append("Past experience title aligns with job title.")
        else:
            reasons.append("Past experience titles don't perfectly align with job title.")
    else:
        reasons.append("Profile has no experience listed.")

    completeness = 0
    if profile.summary: completeness += 5
    if profile.educations: completeness += 5
    if profile.projects: completeness += 5
    if profile.linkedin or profile.github: completeness += 5
    
    score += completeness
    reasons.append(f"Profile completeness contributes {completeness} points. (Fallback Matcher)")

    return min(100, score), " ".join(reasons)
