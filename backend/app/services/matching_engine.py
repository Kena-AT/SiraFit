from dataclasses import dataclass, field
from app.models.profile import Profile
from app.models.job import Job


@dataclass
class ScoringWeights:
    skills_weight: float = 0.5
    experience_weight: float = 0.3
    education_weight: float = 0.2

    def validate(self):
        total = self.skills_weight + self.experience_weight + self.education_weight
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


DEFAULT_WEIGHTS = ScoringWeights()


def _skills_score(profile: Profile, job: Job) -> tuple[int, str]:
    profile_skills = {skill.name.lower() for skill in profile.skills}
    job_tags = job.tags if job.tags else []
    if not job_tags:
        return 100, "No skill requirements specified — defaulting to 100%."
    matches = sum(1 for tag in job_tags if tag.lower() in profile_skills)
    ratio = matches / len(job_tags)
    score = int(ratio * 100)
    return score, (
        f"Matched {matches}/{len(job_tags)} required skills ({score}%)."
    )


def _experience_score(profile: Profile) -> tuple[int, str]:
    if not profile.experiences:
        return 20, "No experience entries on profile (20%)."
    years_total = 0
    for exp in profile.experiences:
        if exp.start_date and exp.end_date:
            delta = exp.end_date - exp.start_date
            years = delta.days / 365.0
            years_total += years
        elif exp.start_date and exp.is_current:
            from datetime import date
            delta = date.today() - exp.start_date
            years = delta.days / 365.0
            years_total += years
    if years_total >= 5:
        return 100, f"Extensive experience ({years_total:.1f} years) — top score."
    elif years_total >= 3:
        return 85, f"Solid experience ({years_total:.1f} years)."
    elif years_total >= 1:
        score = int(60 + (years_total / 5) * 25)
        return score, f"Moderate experience ({years_total:.1f} years)."
    else:
        return 40, "Minimal experience on profile."


def _education_score(profile: Profile) -> tuple[int, str]:
    if not profile.educations:
        return 20, "No education entries on profile."
    levels = {"phd": 100, "master": 90, "bachelor": 75, "associate": 60, "high school": 40}
    best = 20
    for edu in profile.educations:
        degree_lower = (edu.degree or "").lower()
        for keyword, val in levels.items():
            if keyword in degree_lower:
                best = max(best, val)
    return best, (
        f"Highest education level scores {best}%."
    )


def calculate_match_score(
    profile: Profile,
    job: Job,
    weights: ScoringWeights = DEFAULT_WEIGHTS,
) -> dict:
    weights.validate()

    skills_score_val, skills_explanation = _skills_score(profile, job)
    experience_score_val, experience_explanation = _experience_score(profile)
    education_score_val, education_explanation = _education_score(profile)

    breakdown = {
        "skills": skills_score_val,
        "experience": experience_score_val,
        "education": education_score_val,
    }
    score = int(
        skills_score_val * weights.skills_weight
        + experience_score_val * weights.experience_weight
        + education_score_val * weights.education_weight
    )
    explanation = (
        f"Skills ({skills_score_val}%) × {weights.skills_weight} + "
        f"Experience ({experience_score_val}%) × {weights.experience_weight} + "
        f"Education ({education_score_val}%) × {weights.education_weight} = {score}%. "
        f"{skills_explanation} {experience_explanation} {education_explanation}"
    )
    return {"score": score, "breakdown": breakdown, "explanation": explanation}
