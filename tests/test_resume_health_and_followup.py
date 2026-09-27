import json
import uuid
import pytest
from unittest.mock import patch, AsyncMock
from app.models.job import Job, JobApplication, Resume, ResumeVersion
from app.models.profile import Profile, Experience, Skill
from app.models.user import User
from app.services.resume_health import calculate_resume_health
from app.services.follow_up_drafting import draft_stage_follow_up, FollowUpDraftOutput


# ---------------------------------------------------------------------------
# Unit tests: Resume Health Scoring Service
# ---------------------------------------------------------------------------


def test_resume_health_minimal_data():
    minimal_data = {"summary": ""}
    report = calculate_resume_health(minimal_data)
    assert report.overall_score < 50
    assert report.grade in ["D", "C"]
    assert len(report.recommendations) > 0
    assert "completeness" in report.breakdown
    assert len(report.checks) > 0


def test_resume_health_complete_data():
    rich_data = {
        "name": "Jane Developer",
        "email": "jane@example.com",
        "phone": "+1234567890",
        "headline": "Lead Software Engineer",
        "summary": "Accomplished Senior Software Engineer with 7+ years developing scalable architectures.",
        "skills": ["Python", "FastAPI", "React", "Docker", "Kubernetes", "PostgreSQL", "AWS"],
        "experience": [
            {
                "title": "Lead Software Engineer",
                "company": "Tech Innovations Inc.",
                "bullets": [
                    "Engineered distributed microservices, reducing latency by 35% across 2M daily requests.",
                    "Spearheaded cloud migration saving $120,000 annually in infrastructure costs.",
                    "Mentored 6 junior engineers and improved test coverage from 60% to 92%.",
                ],
            }
        ],
        "education": [
            {
                "institution": "State University",
                "degree": "B.S. in Computer Science",
            }
        ],
    }
    report = calculate_resume_health(rich_data)
    assert report.overall_score >= 80
    assert report.grade in ["A+", "A", "B"]
    assert report.breakdown["action_verbs"] > 0
    assert report.breakdown["quantified_metrics"] > 0
    assert report.breakdown["completeness"] >= 20


# ---------------------------------------------------------------------------
# API tests: Resume Health Endpoints
# ---------------------------------------------------------------------------


def test_profile_health_no_profile(client, auth_tokens, db):
    user = db.query(User).filter_by(email="fixture@example.com").first()
    p = db.query(Profile).filter_by(user_id=user.id).first()
    if p:
        db.delete(p)
        db.commit()

    headers = {"Authorization": f"Bearer {auth_tokens['access_token']}"}
    response = client.get("/api/v1/resumes/health/profile", headers=headers)
    assert response.status_code == 404
    assert "Profile not found" in response.json()["detail"]


def test_profile_health_with_profile(client, auth_tokens, db):
    user = db.query(User).filter_by(email="fixture@example.com").first()
    p = db.query(Profile).filter_by(user_id=user.id).first()
    if not p:
        p = Profile(user_id=user.id, email=user.email)
        db.add(p)
        db.commit()
        db.refresh(p)

    p.headline = "Full Stack Engineer"
    p.summary = "Experienced engineer with Python and React for 5+ years."
    db.commit()

    exp = Experience(
        profile_id=p.id,
        title="Developer",
        company="Code Co",
        description="Built fast REST APIs and managed 15+ database servers.",
    )
    sk = Skill(profile_id=p.id, name="Python")
    db.add(exp)
    db.add(sk)
    db.commit()

    headers = {"Authorization": f"Bearer {auth_tokens['access_token']}"}
    response = client.get("/api/v1/resumes/health/profile", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert "grade" in data
    assert "breakdown" in data
    assert "recommendations" in data


def test_resume_version_health(client, auth_tokens, db):
    user = db.query(User).filter_by(email="fixture@example.com").first()
    resume = Resume(user_id=user.id, title="Frontend Resume", content="{\"summary\": \"test\"}")
    db.add(resume)
    db.commit()

    content = {
        "name": "Jane Dev",
        "email": user.email,
        "headline": "Frontend Lead",
        "summary": "Experienced engineer with multiple shipped web apps.",
        "skills": ["TypeScript", "Vue", "Node.js"],
        "experience": [
            {
                "title": "Frontend Lead",
                "company": "Web Solutions",
                "bullets": ["Optimized client bundles by 40%."],
            }
        ],
    }
    v = ResumeVersion(
        resume_id=resume.id,
        version_number=1,
        content=json.dumps(content),
        source_type="base",
        status="completed",
    )
    db.add(v)
    db.commit()

    headers = {"Authorization": f"Bearer {auth_tokens['access_token']}"}
    response = client.get(f"/api/v1/resumes/{resume.id}/health", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_score"] > 0
    assert "grade" in data


# ---------------------------------------------------------------------------
# API tests: AI Follow-up Drafting Endpoint
# ---------------------------------------------------------------------------


def test_follow_up_draft_endpoint(client, auth_tokens, db):
    user = db.query(User).filter_by(email="fixture@example.com").first()

    job = Job(
        external_id=f"ext_{uuid.uuid4().hex[:8]}",
        title="Senior Python Architect",
        company="Apex Systems",
        description="Python backend system development",
    )
    db.add(job)
    db.commit()

    app = JobApplication(
        user_id=user.id,
        job_id=job.id,
        status="interview",
    )
    db.add(app)
    db.commit()

    headers = {"Authorization": f"Bearer {auth_tokens['access_token']}"}

    mock_output = FollowUpDraftOutput(
        subject="Thank You - Interview for Senior Python Architect",
        body="Hi Apex Team, Thank you for taking the time to speak with me today about the Senior Python Architect role.",
        draft_note="Follow up with Apex Team on interview status",
    )
    with patch(
        "app.services.follow_up_drafting.structured_completion_with_fallback",
        new=AsyncMock(return_value=mock_output),
    ):
        response = client.post(f"/api/v1/applications/{app.id}/followup/draft", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "subject" in data
        assert "body" in data
        assert "Apex" in data["body"]


def test_follow_up_draft_fallback(client, auth_tokens, db):
    user = db.query(User).filter_by(email="fixture@example.com").first()

    job = Job(
        external_id=f"ext_{uuid.uuid4().hex[:8]}",
        title="DevOps Engineer",
        company="CloudNet",
        description="Kubernetes management",
    )
    db.add(job)
    db.commit()

    app = JobApplication(
        user_id=user.id,
        job_id=job.id,
        status="applied",
    )
    db.add(app)
    db.commit()

    headers = {"Authorization": f"Bearer {auth_tokens['access_token']}"}

    # Mock structured completion failure to trigger fallback template
    with patch(
        "app.services.follow_up_drafting.structured_completion_with_fallback",
        new=AsyncMock(side_effect=Exception("AI error")),
    ):
        response = client.post(f"/api/v1/applications/{app.id}/followup/draft", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "DevOps Engineer" in data["subject"]
        assert "CloudNet" in data["subject"]
        assert len(data["body"]) > 20
