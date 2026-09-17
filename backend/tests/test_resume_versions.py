import uuid
import json
import pytest
from app.models.job import Job, JobApplication, Resume, ResumeVersion
from app.models.profile import Profile, Experience, Skill
from app.models.user import User
from app.services.resume_diff import compute_resume_diff
from app.services.resume_versioning import (
    create_base_version_from_profile,
    revert_to_version,
    compare_resume_versions,
)


@pytest.fixture
def test_user(db):
    u = User(
        email=f"user_{uuid.uuid4().hex[:8]}@example.com",
        first_name="Alice",
        last_name="Tester",
        hashed_password="hash",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def other_user(db):
    u = User(
        email=f"other_{uuid.uuid4().hex[:8]}@example.com",
        first_name="Bob",
        last_name="Other",
        hashed_password="hash",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def test_profile(db, test_user):
    p = Profile(
        user_id=test_user.id,
        first_name="Alice",
        last_name="Tester",
        headline="Software Engineer",
        summary="Experienced backend engineer with Python expertise.",
        email=test_user.email,
        phone="+1234567890",
        location="Remote",
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    exp = Experience(
        profile_id=p.id,
        title="Senior Developer",
        company="Tech Corp",
        location="Remote",
        description="Built distributed microservices in Python.\nScaled PostgreSQL queries.",
        is_current=True,
    )
    skill = Skill(
        profile_id=p.id,
        name="Python",
    )
    db.add(exp)
    db.add(skill)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def test_job(db):
    j = Job(
        title="Backend Engineer",
        company="DreamWorks Inc",
        description="Looking for senior Python developer.",
        location="Remote",
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


@pytest.fixture
def test_resume(db, test_user):
    r = Resume(
        user_id=test_user.id,
        title="My Software Resume",
        content="Initial content",
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


# ---------------------------------------------------------------------------
# Unit tests: Base Resume & Invariant
# ---------------------------------------------------------------------------


def test_create_base_version_from_profile(db, test_resume, test_profile):
    base_v = create_base_version_from_profile(db, test_resume, test_profile)
    assert base_v is not None
    assert base_v.source_type == "base"
    assert base_v.parent_version_id is None
    assert base_v.job_id is None
    assert base_v.version_number == 1

    content_data = json.loads(base_v.content)
    assert content_data["name"] == "Alice Tester"
    assert "Python" in content_data["skills"]
    assert len(content_data["experience"]) == 1
    assert content_data["experience"][0]["company"] == "Tech Corp"

    # Invariant: Calling again returns the existing base snapshot
    base_v2 = create_base_version_from_profile(db_session, test_resume, test_profile)
    assert base_v2.id == base_v.id


# ---------------------------------------------------------------------------
# Unit tests: Semantic Diff Service
# ---------------------------------------------------------------------------


def test_resume_diff_identical():
    c = {
        "summary": "Full stack engineer",
        "skills": ["Python", "FastAPI", "React"],
        "experience": [
            {
                "title": "Engineer",
                "company": "Company A",
                "bullets": ["Wrote code", "Deployed apps"],
            }
        ],
        "projects": [{"name": "Project 1", "description": "Desc"}],
        "education": [{"institution": "Uni", "degree": "BS"}],
    }
    diff = compute_resume_diff(
        from_version_id=uuid.uuid4(),
        to_version_id=uuid.uuid4(),
        from_version_number=1,
        to_version_number=2,
        from_content_raw=c,
        to_content_raw=c,
    )
    assert diff.has_changes is False
    assert diff.summary.added == 0
    assert diff.summary.removed == 0
    assert diff.summary.changed == 0
    assert diff.sections.summary.changed is False


def test_resume_diff_semantic_changes():
    c1 = {
        "summary": "Junior engineer",
        "skills": ["Python", "Docker"],
        "experience": [
            {
                "title": "Dev",
                "company": "Acme",
                "period": "2020-2021",
                "bullets": ["Fixed bugs", "Wrote tests"],
            }
        ],
    }
    c2 = {
        "summary": "Senior engineer",
        "skills": ["Python", "Kubernetes", "AWS"],  # removed Docker, added K8s & AWS
        "experience": [
            {
                "title": "Dev",
                "company": "Acme",
                "period": "2020-2022",  # changed period
                "bullets": ["Fixed bugs", "Architected cloud infra"],  # -Wrote tests, +Architected...
            }
        ],
    }
    diff = compute_resume_diff(
        from_version_id=uuid.uuid4(),
        to_version_id=uuid.uuid4(),
        from_version_number=1,
        to_version_number=2,
        from_content_raw=c1,
        to_content_raw=c2,
    )
    assert diff.has_changes is True
    assert diff.sections.summary.changed is True
    assert diff.sections.summary.from_text == "Junior engineer"
    assert diff.sections.summary.to_text == "Senior engineer"

    assert "Kubernetes" in diff.sections.skills.added
    assert "AWS" in diff.sections.skills.added
    assert "Docker" in diff.sections.skills.removed
    assert "Python" in diff.sections.skills.preserved

    exp = diff.sections.experience[0]
    assert exp.status == "modified"
    assert "Architected cloud infra" in exp.bullets_added
    assert "Wrote tests" in exp.bullets_removed
    assert "Fixed bugs" in exp.bullets_preserved


# ---------------------------------------------------------------------------
# Unit tests: Revert & Lineage
# ---------------------------------------------------------------------------


def test_revert_version_flow(db, test_user, test_resume, test_profile, test_job):
    # 1. Base version
    base_v = create_base_version_from_profile(db, test_resume, test_profile)

    # 2. Tailored version v2
    tailored_v = ResumeVersion(
        resume_id=test_resume.id,
        version_number=2,
        content=json.dumps({"summary": "Tailored for DreamWorks", "skills": ["Python", "AI"]}),
        job_id=test_job.id,
        parent_version_id=base_v.id,
        source_type="tailored",
        score=92,
        status="completed",
    )
    db.add(tailored_v)
    db.commit()

    # 3. Another tailored version v3
    v3 = ResumeVersion(
        resume_id=test_resume.id,
        version_number=3,
        content=json.dumps({"summary": "Tailored for Other Job", "skills": ["Go"]}),
        job_id=None,
        parent_version_id=tailored_v.id,
        source_type="tailored",
        score=75,
        status="completed",
    )
    db.add(v3)
    db.commit()

    # 4. Revert to tailored_v (v2)
    reverted_v = revert_to_version(
        db=db,
        resume_id=test_resume.id,
        target_version_id=tailored_v.id,
        current_user_id=test_user.id,
    )

    # Verify immutability & metadata
    assert reverted_v.id != tailored_v.id
    assert reverted_v.version_number == 4
    assert reverted_v.source_type == "revert"
    assert reverted_v.parent_version_id == tailored_v.id
    assert reverted_v.content == tailored_v.content
    assert reverted_v.score == tailored_v.score
    assert reverted_v.job_id == tailored_v.job_id

    # Verify target was NOT changed
    reloaded_target = db.query(ResumeVersion).filter(ResumeVersion.id == tailored_v.id).first()
    assert reloaded_target.version_number == 2
    assert reloaded_target.source_type == "tailored"


# ---------------------------------------------------------------------------
# Unit tests: JobApplication tracking
# ---------------------------------------------------------------------------


def test_job_application_version_tracking(db, test_user, test_job, test_resume, test_profile):
    base_v = create_base_version_from_profile(db, test_resume, test_profile)

    app = JobApplication(
        user_id=test_user.id,
        job_id=test_job.id,
        status="applied",
        resume_version_id=base_v.id,
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    assert app.resume_version_id == base_v.id
    assert app.resume_version.id == base_v.id
