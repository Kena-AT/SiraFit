from app.models.profile import Profile
from app.models.job import Job

def calculate_match_score(profile: Profile, job: Job) -> dict:
    # Deterministic scoring logic based on skills, experience, etc.
    # This is a simplified version for the prototype.
    
    score = 0
    breakdown = {
        "skills": 0,
        "experience": 0,
        "education": 0
    }
    
    # Simple skill matching
    profile_skills = {skill.name.lower() for skill in profile.skills}
    job_tags = job.tags if job.tags else []
    
    matching_skills = [skill for skill in job_tags if skill.lower() in profile_skills]
    if job_tags:
        breakdown["skills"] = int((len(matching_skills) / len(job_tags)) * 100)
    else:
        breakdown["skills"] = 100 # No requirements means 100% match

    # Simple experience matching (just checking if experience exists for now)
    if profile.experiences:
        breakdown["experience"] = 80
    else:
        breakdown["experience"] = 20

    # Education matching
    if profile.educations:
        breakdown["education"] = 80
    else:
        breakdown["education"] = 20
        
    # Overall score
    score = int((breakdown["skills"] * 0.5 + breakdown["experience"] * 0.3 + breakdown["education"] * 0.2))
    
    explanation = f"Based on your profile, your skills match {breakdown['skills']}% of the job requirements."
    
    return {
        "score": score,
        "breakdown": breakdown,
        "explanation": explanation
    }
