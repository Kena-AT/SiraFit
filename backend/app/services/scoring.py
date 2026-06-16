import re
from typing import Tuple
from app.models.profile import Profile
from app.models.job import Job

def calculate_match_score(profile: Profile, job: Job) -> Tuple[int, str]:
    """
    A placeholder scoring algorithm that compares a user's profile with a job description.
    Returns a tuple of (score 0-100, reason string).
    """
    if not profile or not job:
        return 0, "Missing profile or job data."

    score = 0
    reasons = []

    job_text = f"{job.title} {job.description or ''} {' '.join(job.tags or [])}".lower()
    
    # 1. Skill Matching (up to 50 points)
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

    # 2. Experience Title Matching (up to 30 points)
    exp_matched = False
    if profile.experiences:
        for exp in profile.experiences:
            # simple keyword match from job title to experience title
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

    # 3. Base completeness (up to 20 points)
    completeness = 0
    if profile.summary: completeness += 5
    if profile.educations: completeness += 5
    if profile.projects: completeness += 5
    if profile.linkedin or profile.github: completeness += 5
    
    score += completeness
    reasons.append(f"Profile completeness contributes {completeness} points.")

    reason_str = " ".join(reasons)
    return min(100, score), reason_str
