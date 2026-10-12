import uuid
import pytest
from app.models.job import Job, JobApplication
from app.models.user import User
from app.services.matching_engine import calculate_public_match


# ---------------------------------------------------------------------------
# Unit tests: Public Match Calculation
# ---------------------------------------------------------------------------


def test_calculate_public_match_deterministic():
    resume_text = """
    Jane Doe - Senior Full Stack Engineer
    Summary: 6+ years experience building cloud microservices with Python, FastAPI, React, and PostgreSQL.
    Experience:
    Tech Innovators (2020 - Present) - Lead Engineer
    - Scaled Docker and Kubernetes infrastructure on AWS.
    - Mentored 4 engineers and improved release velocity by 40%.
    Education: B.S. in Computer Science
    Skills: Python, TypeScript, React, Docker, Kubernetes, AWS, PostgreSQL, Redis
    """

    job_description = """
    We are looking for a Senior Backend Developer proficient in Python, FastAPI, PostgreSQL, and Kubernetes.
    Experience with AWS and Docker is required. Minimum 4 years experience required.
    """

    result = calculate_public_match(
        resume_text=resume_text,
        job_description=job_description,
        job_title="Senior Backend Developer",
        job_company="CloudTech Corp",
    )

    assert result["overall_score"] >= 70
    assert result["verdict"] in ["Strong Fit", "Good Fit"]
    assert "python" in [s.lower() for s in result["matching_skills"]]
    assert "breakdown" in result
    assert result["breakdown"]["skills"] > 50
    assert len(result["recommendations"]) > 0


def test_calculate_public_match_minimal_overlap():
    resume_text = "Junior Graphic Designer with 1 year experience in Photoshop, Illustrator, and Figma."
    job_description = "Principal Distributed Systems Engineer. Requires Go, Rust, gRPC, and Kubernetes."

    result = calculate_public_match(
        resume_text=resume_text,
        job_description=job_description,
        job_title="Principal Distributed Systems Engineer",
    )

    assert result["overall_score"] < 60
    assert result["verdict"] in ["Moderate Fit", "Needs Tailoring"]
    assert len(result["missing_skills"]) > 0


# ---------------------------------------------------------------------------
# API tests: Public Match Score Endpoint
# ---------------------------------------------------------------------------


def test_public_match_endpoint_success(client):
    payload = {
        "resume_text": "Experienced Python and React developer with 5+ years building web applications with Docker and AWS.",
        "job_description": "Looking for a Python software engineer with React and Docker experience for our fast-paced team.",
        "job_title": "Software Engineer",
        "job_company": "Startup Labs",
    }
    # No auth header needed (public endpoint)
    response = client.post("/api/v1/jobs/match-public", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert "verdict" in data
    assert "matching_skills" in data
    assert "breakdown" in data
    assert "recommendations" in data


def test_public_match_endpoint_validation_error(client):
    # Text too short (< 20 chars)
    payload = {
        "resume_text": "Too short",
        "job_description": "Short",
    }
    response = client.post("/api/v1/jobs/match-public", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# API tests: Applications Filtering and Search
# ---------------------------------------------------------------------------


def test_applications_status_and_search_filtering(client, auth_tokens, db):
    user = db.query(User).filter_by(email="fixture@example.com").first()

    job1 = Job(
        external_id=f"ext_{uuid.uuid4().hex[:8]}",
        title="Backend Python Engineer",
        company="Stripe",
        description="Python services",
    )
    job2 = Job(
        external_id=f"ext_{uuid.uuid4().hex[:8]}",
        title="Frontend React Developer",
        company="Shopify",
        description="React and TypeScript",
    )
    db.add(job1)
    db.add(job2)
    db.commit()

    app1 = JobApplication(
        user_id=user.id,
        job_id=job1.id,
        status="applied",
    )
    app2 = JobApplication(
        user_id=user.id,
        job_id=job2.id,
        status="interview",
    )
    db.add(app1)
    db.add(app2)
    db.commit()

    headers = {"Authorization": f"Bearer {auth_tokens['access_token']}"}

    # 1. Filter by status=interview
    res_status = client.get("/api/v1/applications?status=interview", headers=headers)
    assert res_status.status_code == 200
    apps_interview = res_status.json()
    assert len(apps_interview) == 1
    assert apps_interview[0]["status"] == "interview"
    assert apps_interview[0]["job"]["company"] == "Shopify"

    # 2. Search by company "Stripe"
    res_search = client.get("/api/v1/applications?search=Stripe", headers=headers)
    assert res_search.status_code == 200
    apps_stripe = res_search.json()
    assert len(apps_stripe) == 1
    assert apps_stripe[0]["job"]["company"] == "Stripe"

    # 3. Search by title "React"
    res_title = client.get("/api/v1/applications?search=React", headers=headers)
    assert res_title.status_code == 200
    apps_react = res_title.json()
    assert len(apps_react) == 1
    assert apps_react[0]["job"]["title"] == "Frontend React Developer"
