import io
import uuid
from datetime import datetime, timedelta, timezone
import pytest
import openpyxl

from app.models.job import ApplicationEvent, Job, JobApplication
from app.models.profile import Profile, Skill
from app.models.skill_taxonomy import SkillTaxonomy
from app.services.analytics import (
    compute_salary_benchmarks,
    compute_skills_gap,
    compute_stall_insights,
    generate_analytics_excel,
    generate_analytics_metrics,
    normalize_job_role,
)
from app.services.skill_taxonomy import seed_skill_taxonomy


def _create_user(client, db):
    email = f"test_analytics_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "ValidPass123!#"
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": pwd, "full_name": "Analytics Tester"},
    )
    assert r.status_code == 201, r.text
    user_data = r.json()
    user_id = uuid.UUID(user_data["id"])

    # Mark verified in db
    from app.models.user import User
    u = db.query(User).filter(User.id == user_id).first()
    if u:
        u.is_verified = True
        db.commit()

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": pwd},
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return user_id, headers


class TestSalaryBenchmarks:
    def test_normalize_job_role(self):
        assert normalize_job_role("Senior Backend Software Engineer") == "Backend Engineer"
        assert normalize_job_role("Junior Frontend Developer") == "Frontend Engineer"
        assert normalize_job_role("Staff Full Stack Engineer") == "Full Stack Engineer"
        assert normalize_job_role("DevOps / SRE Lead") == "DevOps Engineer"
        assert normalize_job_role("Data Platform Engineer") == "Data Engineer"
        assert normalize_job_role("iOS Mobile Developer") == "Mobile Engineer"
        assert normalize_job_role("Product Manager") == "Product Manager"
        assert normalize_job_role("") == "Software Engineer"

    def test_compute_salary_benchmarks_sample_threshold(self):
        # 4 samples: less than SALARY_BENCHMARK_MIN_SAMPLES (5) -> percentiles are None
        jobs = [
            Job(
                id=uuid.uuid4(),
                external_id=f"job-{i}",
                title="Backend Engineer",
                company="Acme Corp",
                salary_min=100000 + i * 10000,
                salary_max=150000 + i * 10000,
                currency="USD",
            )
            for i in range(4)
        ]
        benchmarks = compute_salary_benchmarks(jobs)
        assert len(benchmarks) == 1
        b = benchmarks[0]
        assert b["role"] == "Backend Engineer"
        assert b["currency"] == "USD"
        assert b["sample_size"] == 4
        assert b["min_p50"] is None
        assert b["max_p50"] is None

        # Add 5th job -> percentiles are computed
        jobs.append(
            Job(
                id=uuid.uuid4(),
                external_id="job-4",
                title="Backend Engineer",
                company="Acme Corp",
                salary_min=140000,
                salary_max=190000,
                currency="USD",
            )
        )
        benchmarks_5 = compute_salary_benchmarks(jobs)
        assert len(benchmarks_5) == 1
        b5 = benchmarks_5[0]
        assert b5["sample_size"] == 5
        assert b5["min_p50"] is not None
        assert b5["max_p50"] is not None
        assert b5["min_p25"] is not None
        assert b5["max_p75"] is not None
        assert b5["min_p50"] <= b5["max_p50"]

    def test_salary_benchmarks_currency_separation(self):
        jobs = [
            Job(
                id=uuid.uuid4(),
                external_id=f"usd-{i}",
                title="Frontend Developer",
                company="US Inc",
                salary_min=90000,
                salary_max=120000,
                currency="USD",
            )
            for i in range(5)
        ] + [
            Job(
                id=uuid.uuid4(),
                external_id=f"eur-{i}",
                title="Frontend Developer",
                company="EU Gmbh",
                salary_min=60000,
                salary_max=80000,
                currency="EUR",
            )
            for i in range(5)
        ]
        benchmarks = compute_salary_benchmarks(jobs)
        assert len(benchmarks) == 2
        currencies = {b["currency"] for b in benchmarks}
        assert currencies == {"USD", "EUR"}

    def test_salary_benchmarks_invalid_values_filtered(self):
        jobs = [
            # Invalid: min > max
            Job(
                id=uuid.uuid4(),
                external_id="bad-1",
                title="Backend Engineer",
                company="Bad",
                salary_min=200000,
                salary_max=100000,
                currency="USD",
            ),
            # Invalid: negative
            Job(
                id=uuid.uuid4(),
                external_id="bad-2",
                title="Backend Engineer",
                company="Bad",
                salary_min=-50000,
                currency="USD",
            ),
            # Valid min only
            Job(
                id=uuid.uuid4(),
                external_id="good-1",
                title="Backend Engineer",
                company="Good",
                salary_min=110000,
                currency="USD",
            ),
        ]
        benchmarks = compute_salary_benchmarks(jobs)
        assert len(benchmarks) == 1
        assert benchmarks[0]["sample_size"] == 1


class TestSkillsGapAnalysis:
    def test_skills_gap_alias_resolution_and_profile_exclusion(self, db):
        seed_skill_taxonomy(db)
        user_id = uuid.uuid4()

        # Create user profile with "Python" and "PostgreSQL"
        profile = Profile(id=uuid.uuid4(), user_id=user_id, revision=1)
        db.add(profile)
        db.commit()

        s1 = Skill(profile_id=profile.id, name="Python")
        s2 = Skill(profile_id=profile.id, name="PostgreSQL")
        db.add_all([s1, s2])
        db.commit()

        # Jobs requiring Docker, Postgres (alias of PostgreSQL), and React
        jobs = [
            Job(
                id=uuid.uuid4(),
                external_id="job-1",
                title="Fullstack",
                company="A",
                tags=["Docker", "Postgres", "Python"],
            ),
            Job(
                id=uuid.uuid4(),
                external_id="job-2",
                title="Fullstack",
                company="B",
                tags=["Docker", "React", "Python"],
            ),
            Job(
                id=uuid.uuid4(),
                external_id="job-3",
                title="DevOps",
                company="C",
                tags=["Docker"],
            ),
        ]
        for j in jobs:
            db.add(j)
        db.commit()

        gap_resp = compute_skills_gap(db, user_id, jobs)
        assert gap_resp["analyzed_jobs"] == 3
        assert gap_resp["current_skill_count"] == 2

        skills = {item["skill"]: item for item in gap_resp["skills"]}
        # Python and PostgreSQL (including alias Postgres) must NOT be in the gap
        assert "Python" not in skills
        assert "PostgreSQL" not in skills
        assert "Postgres" not in skills

        # Docker and React must be present
        assert "Docker" in skills
        assert skills["Docker"]["frequency"] == 3
        assert skills["Docker"]["percentage"] == 100.0
        assert skills["Docker"]["priority"] is True  # 100% >= 20%

        assert "React" in skills
        assert skills["React"]["frequency"] == 1
        assert skills["React"]["percentage"] == round(1 / 3 * 100, 1)


class TestStallInsights:
    def test_stall_insights_stage_duration_and_drop_off(self, db):
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        applications = []
        for i in range(4):
            app = JobApplication(
                id=uuid.uuid4(),
                user_id=user_id,
                job_id=uuid.uuid4(),
                status="interview" if i < 3 else "rejected",
                created_at=now - timedelta(days=20),
            )
            applications.append(app)
            db.add(app)
        db.commit()

        # Simulate transitions: applied -> screening (after 24 hrs) -> interview (after 48 hrs)
        for i, app in enumerate(applications):
            # Event 1: entered screening from applied
            e1 = ApplicationEvent(
                application_id=app.id,
                user_id=user_id,
                event_type="status_change",
                title="Status changed to screening",
                event_metadata={"from_status": "applied", "to_status": "screening"},
                occurred_at=now - timedelta(days=19),
            )
            # Event 2: entered interview or rejected
            to_st = "interview" if i < 3 else "rejected"
            e2 = ApplicationEvent(
                application_id=app.id,
                user_id=user_id,
                event_type="status_change",
                title=f"Status changed to {to_st}",
                event_metadata={"from_status": "screening", "to_status": to_st},
                occurred_at=now - timedelta(days=17),  # 48 hours in screening
            )
            # Add an unrelated event that should be ignored
            unrelated = ApplicationEvent(
                application_id=app.id,
                user_id=user_id,
                event_type="note_added",
                title="Note added",
                occurred_at=now - timedelta(days=18),
            )
            db.add_all([e1, e2, unrelated])
        db.commit()

        insights = compute_stall_insights(db, user_id, applications)
        assert insights["total_applications"] == 4
        stages_by_name = {s["stage"]: s for s in insights["stages"]}

        screening_stat = stages_by_name["screening"]
        assert screening_stat["entered_count"] == 4
        assert screening_stat["progressed_count"] == 3
        assert screening_stat["dropped_count"] == 1
        assert screening_stat["drop_off_rate"] == 0.25
        # 4 samples >= 3 threshold: median duration in hours should be around 48.0 hrs
        assert screening_stat["median_duration_hours"] is not None
        assert 47.0 <= screening_stat["median_duration_hours"] <= 49.0
        assert screening_stat["duration_sample_size"] == 4


class TestAnalyticsEndpointsAndExport:
    def test_get_metrics_expanded_payload(self, client, db):
        user_id, headers = _create_user(client, db)
        resp = client.get("/api/v1/analytics/metrics", headers=headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        # Legacy fields
        assert "total_applications" in data
        assert "interview_rate" in data
        assert "conversion_funnel" in data

        # Sprint 10 fields
        assert "salary_benchmarks" in data
        assert "skills_gap_analysis" in data
        assert "stall_insights" in data

    def test_export_analytics_xlsx(self, client, db):
        user_id, headers = _create_user(client, db)

        # Create a job and an application so export has data
        job = Job(
            id=uuid.uuid4(),
            external_id=f"exp-job-{uuid.uuid4().hex[:6]}",
            title="Backend Engineer",
            company="Globex Corp",
            salary_min=120000,
            salary_max=160000,
            currency="USD",
            tags=["Python", "FastAPI"],
        )
        db.add(job)
        db.commit()

        app = JobApplication(
            id=uuid.uuid4(),
            user_id=user_id,
            job_id=job.id,
            status="applied",
        )
        db.add(app)
        db.commit()

        resp = client.get("/api/v1/analytics/export?format=xlsx", headers=headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert 'attachment; filename="sirafit_analytics_export.xlsx"' in resp.headers["content-disposition"]

        # Validate excel structure with openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(resp.content))
        expected_sheets = [
            "Overview",
            "Salary Benchmarks",
            "Skills Gap",
            "Stall Insights",
            "Conversion Funnel",
        ]
        for sheet in expected_sheets:
            assert sheet in wb.sheetnames

    def test_multi_tenant_isolation(self, client, db):
        user_a_id, headers_a = _create_user(client, db)
        user_b_id, headers_b = _create_user(client, db)

        job = Job(
            id=uuid.uuid4(),
            external_id=f"iso-job-{uuid.uuid4().hex[:6]}",
            title="Secret Role",
            company="TopSecret",
        )
        db.add(job)
        db.commit()

        # User A has 1 application
        app_a = JobApplication(
            id=uuid.uuid4(),
            user_id=user_a_id,
            job_id=job.id,
            status="offer",
        )
        db.add(app_a)
        db.commit()

        # User B should see 0 applications and 0 offer rate
        resp_b = client.get("/api/v1/analytics/metrics", headers=headers_b)
        assert resp_b.status_code == 200
        data_b = resp_b.json()
        assert data_b["total_applications"] == 0
        assert data_b["offer_rate"] == 0.0
