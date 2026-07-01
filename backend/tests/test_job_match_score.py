import pytest
from unittest.mock import MagicMock
from datetime import date
from app.models.job import Job
from app.models.profile import Profile, Experience, Education, Skill
from app.services.matching_engine import calculate_match_score, ScoringWeights


# ── Helpers ──

def _make_profile(skills: list[str] | None = None,
                  experiences: int = 0,
                  edu_years: int = 0,
                  edu_degree: str = "") -> MagicMock:
    profile = MagicMock(spec=Profile)

    profile.skills = []
    if skills:
        for name in skills:
            s = MagicMock(spec=Skill)
            s.name = name
            profile.skills.append(s)

    profile.experiences = []
    for i in range(experiences):
        exp = MagicMock(spec=Experience)
        exp.start_date = date(2018, 1, 1)
        exp.end_date = date(2024, 6, 1)
        exp.is_current = False
        profile.experiences.append(exp)

    profile.educations = []
    if edu_years > 0:
        for _ in range(1):
            edu = MagicMock(spec=Education)
            edu.degree = edu_degree
            edu.start_date = date(2020, 9, 1)
            edu.end_date = date(2024, 6, 1)
            profile.educations.append(edu)

    return profile


def _make_job(tags: list[str] | None = None) -> MagicMock:
    job = MagicMock(spec=Job)
    job.title = "Engineer"
    job.company = "Acme"
    job.tags = tags or []
    return job


# ── Tests ──

class TestMatchingEngine:

    def test_perfect_match(self):
        profile = _make_profile(skills=["python", "fastapi", "docker"], experiences=3, edu_years=4, edu_degree="Bachelor")
        job = _make_job(tags=["python", "fastapi", "docker"])
        result = calculate_match_score(profile, job)
        assert result["score"] >= 90
        assert result["breakdown"]["skills"] == 100

    def test_no_skills_match(self):
        profile = _make_profile(skills=["java"], experiences=1, edu_years=1, edu_degree="Bachelor")
        job = _make_job(tags=["python", "fastapi", "docker"])
        result = calculate_match_score(profile, job)
        assert result["breakdown"]["skills"] == 0
        assert result["score"] < 50

    def test_partial_skills_match(self):
        profile = _make_profile(skills=["python", "go"], experiences=1, edu_years=1, edu_degree="Bachelor")
        job = _make_job(tags=["python", "fastapi", "docker", "kubernetes"])
        result = calculate_match_score(profile, job)
        assert result["breakdown"]["skills"] == 25  # 1/4

    def test_no_job_tags(self):
        profile = _make_profile(skills=[], experiences=0, edu_years=0, edu_degree="")
        job = _make_job(tags=[])
        result = calculate_match_score(profile, job)
        assert result["breakdown"]["skills"] == 100  # no requirements = 100%

    def test_no_experience(self):
        profile = _make_profile(skills=["python"], experiences=0, edu_years=0, edu_degree="")
        job = _make_job(tags=["python"])
        result = calculate_match_score(profile, job)
        assert result["breakdown"]["experience"] == 20
        assert "no experience" in result["explanation"].lower()

    def test_no_education(self):
        profile = _make_profile(skills=["python"], experiences=1, edu_years=0, edu_degree="")
        job = _make_job(tags=["python"])
        result = calculate_match_score(profile, job)
        assert result["breakdown"]["education"] == 20

    def test_no_skills_and_no_experience_and_no_education(self):
        profile = _make_profile(skills=[], experiences=0, edu_years=0, edu_degree="")
        job = _make_job(tags=["python"])
        result = calculate_match_score(profile, job)
        assert result["score"] >= 0
        assert result["breakdown"]["skills"] == 0
        assert result["breakdown"]["experience"] == 20
        assert result["breakdown"]["education"] == 20

    def test_custom_weights(self):
        profile = _make_profile(skills=["python"], experiences=1, edu_years=1, edu_degree="Bachelor")
        job = _make_job(tags=["python"])
        weights = ScoringWeights(skills_weight=1.0, experience_weight=0.0, education_weight=0.0)
        result = calculate_match_score(profile, job, weights=weights)
        assert result["score"] == result["breakdown"]["skills"]  # only skills matters

    def test_invalid_weights_raises(self):
        profile = _make_profile(skills=[], experiences=0, edu_years=0, edu_degree="")
        job = _make_job(tags=[])
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            calculate_match_score(profile, job, weights=ScoringWeights(0.5, 0.5, 0.5))

    def test_case_insensitive_skill_matching(self):
        profile = _make_profile(skills=["Python", "FastAPI"])
        job = _make_job(tags=["python", "fastapi"])
        result = calculate_match_score(profile, job)
        assert result["breakdown"]["skills"] == 100

    def test_explanation_contains_all_dimensions(self):
        profile = _make_profile(skills=["python"], experiences=1, edu_years=1, edu_degree="Bachelor")
        job = _make_job(tags=["python"])
        result = calculate_match_score(profile, job)
        expl = result["explanation"]
        assert "skills" in expl
        assert "experience" in expl
        assert "education" in expl
