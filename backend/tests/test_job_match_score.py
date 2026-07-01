import pytest
from unittest.mock import MagicMock
from app.models.job import Job
from app.models.profile import Profile
from app.services.matching_engine import calculate_match_score

def test_calculate_match_score():
    # Setup test data
    job = Job(
        title="Python Engineer",
        company="Acme",
        tags=["python", "fastapi"]
    )
    
    # Mock profile with matching skills
    profile = MagicMock(spec=Profile)
    
    # Mock skills
    skill1 = MagicMock()
    skill1.name = "Python"
    skill2 = MagicMock()
    skill2.name = "FastAPI"
    profile.skills = [skill1, skill2]
    
    # Mock experience and education
    profile.experiences = [MagicMock()]
    profile.educations = [MagicMock()]
    
    result = calculate_match_score(profile, job)
    
    assert "score" in result
    assert result["score"] > 0
    assert result["breakdown"]["skills"] == 100
    assert result["breakdown"]["experience"] == 80
    assert result["breakdown"]["education"] == 80
