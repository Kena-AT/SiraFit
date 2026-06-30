"""
Tests for job search, filtering, sorting, and pagination.
"""

import uuid
import pytest
from app.models.job import Job


class TestJobSearch:
    """Tests for job search functionality."""

    def test_search_by_title(self, client, auth_tokens, db):
        # Create test jobs
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="Senior Python Engineer",
            company="TechCorp",
            source="linkedin",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Java Developer",
            company="DevCo",
            source="indeed",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?search=Python",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any("Python" in job["title"] for job in data["jobs"])

    def test_search_by_company(self, client, auth_tokens, db):
        job = Job(
            external_id=str(uuid.uuid4()),
            title="Software Engineer",
            company="Unique Company Name",
            source="url",
        )
        db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?search=Unique Company",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any("Unique Company" in job["company"] for job in data["jobs"])

    def test_search_by_description(self, client, auth_tokens, db):
        job = Job(
            external_id=str(uuid.uuid4()),
            title="Developer",
            company="TestCo",
            description="We need someone with Kubernetes and Docker experience",
            source="lever",
        )
        db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?search=Kubernetes",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_search_case_insensitive(self, client, auth_tokens, db):
        job = Job(
            external_id=str(uuid.uuid4()),
            title="React Developer",
            company="Frontend Inc",
            source="greenhouse",
        )
        db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?search=react",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_search_no_results(self, client, auth_tokens):
        resp = client.get(
            "/api/v1/jobs?search=nonexistentxyzabc123",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert len(data["jobs"]) == 0


class TestJobFiltering:
    """Tests for job filtering functionality."""

    def test_filter_by_company(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="Engineer A",
            company="FilterTestCo",
            source="linkedin",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Engineer B",
            company="OtherCo",
            source="indeed",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?company=FilterTestCo",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all("FilterTestCo" in job["company"] for job in data["jobs"])

    def test_filter_by_location(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="Remote Engineer",
            company="RemoteCo",
            location="San Francisco, CA",
            source="lever",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Onsite Engineer",
            company="OnsiteCo",
            location="New York, NY",
            source="greenhouse",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?location=San Francisco",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all("San Francisco" in (job["location"] or "") for job in data["jobs"])

    def test_filter_by_source(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="LinkedIn Job",
            company="LinkedInCo",
            source="linkedin",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Indeed Job",
            company="IndeedCo",
            source="indeed",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?source=linkedin",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(job["source"] == "linkedin" for job in data["jobs"])

    def test_filter_by_tags(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="Python Developer",
            company="PythonCo",
            tags=["python", "django", "postgresql"],
            source="url",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="JS Developer",
            company="JSCo",
            tags=["javascript", "react"],
            source="url",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?tags=python",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all("python" in job["tags"] for job in data["jobs"])

    def test_filter_by_multiple_tags(self, client, auth_tokens, db):
        job = Job(
            external_id=str(uuid.uuid4()),
            title="Full Stack Developer",
            company="FullStackCo",
            tags=["python", "react", "postgresql"],
            source="lever",
        )
        db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?tags=python,react",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(
            "python" in job["tags"] and "react" in job["tags"]
            for job in data["jobs"]
        )

    def test_filter_by_min_salary(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="High Paying Job",
            company="HighPayCo",
            salary_min=150000,
            salary_max=200000,
            source="linkedin",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Low Paying Job",
            company="LowPayCo",
            salary_min=50000,
            salary_max=70000,
            source="indeed",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?min_salary=100000",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for job in data["jobs"]:
            assert (
                (job["salary_min"] and job["salary_min"] >= 100000) or
                (job["salary_max"] and job["salary_max"] >= 100000)
            )

    def test_filter_by_max_salary(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="Mid Paying Job",
            company="MidPayCo",
            salary_min=80000,
            salary_max=100000,
            source="greenhouse",
        )
        db.add(job1)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?max_salary=120000",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for job in data["jobs"]:
            if job["salary_max"]:
                assert job["salary_max"] <= 120000 or job["salary_min"] <= 120000

    def test_combined_filters(self, client, auth_tokens, db):
        job = Job(
            external_id=str(uuid.uuid4()),
            title="Senior Python Engineer",
            company="TestCorp",
            location="Remote",
            tags=["python", "aws"],
            salary_min=120000,
            salary_max=180000,
            source="lever",
        )
        db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?company=TestCorp&location=Remote&tags=python&source=lever",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1


class TestJobSorting:
    """Tests for job sorting functionality."""

    def test_sort_by_created_at_desc(self, client, auth_tokens, db):
        # Jobs are created in sequence, newest should be first
        resp = client.get(
            "/api/v1/jobs?sort_by=created_at&sort_order=desc",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        if len(data["jobs"]) > 1:
            dates = [job["created_at"] for job in data["jobs"]]
            assert dates == sorted(dates, reverse=True)

    def test_sort_by_created_at_asc(self, client, auth_tokens, db):
        resp = client.get(
            "/api/v1/jobs?sort_by=created_at&sort_order=asc",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        if len(data["jobs"]) > 1:
            dates = [job["created_at"] for job in data["jobs"]]
            assert dates == sorted(dates)

    def test_sort_by_company_asc(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="Job A",
            company="Zebra Corp",
            source="linkedin",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Job B",
            company="Apple Corp",
            source="indeed",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?sort_by=company&sort_order=asc",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        if len(data["jobs"]) > 1:
            companies = [job["company"] for job in data["jobs"]]
            assert companies == sorted(companies)

    def test_sort_by_title_desc(self, client, auth_tokens, db):
        job1 = Job(
            external_id=str(uuid.uuid4()),
            title="A Engineer",
            company="TestCo",
            source="lever",
        )
        job2 = Job(
            external_id=str(uuid.uuid4()),
            title="Z Engineer",
            company="TestCo",
            source="greenhouse",
        )
        db.add_all([job1, job2])
        db.commit()

        resp = client.get(
            "/api/v1/jobs?sort_by=title&sort_order=desc",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        if len(data["jobs"]) > 1:
            titles = [job["title"] for job in data["jobs"]]
            assert titles == sorted(titles, reverse=True)


class TestJobPagination:
    """Tests for job pagination functionality."""

    def test_pagination_first_page(self, client, auth_tokens, db):
        # Create 10 jobs
        for i in range(10):
            job = Job(
                external_id=str(uuid.uuid4()),
                title=f"Job {i}",
                company=f"Company {i}",
                source="url",
            )
            db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?skip=0&limit=5",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["jobs"]) <= 5
        assert data["skip"] == 0
        assert data["limit"] == 5
        assert data["total"] >= 10

    def test_pagination_second_page(self, client, auth_tokens, db):
        resp = client.get(
            "/api/v1/jobs?skip=5&limit=5",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["skip"] == 5
        assert data["limit"] == 5

    def test_pagination_limit_validation(self, client, auth_tokens):
        # Test max limit
        resp = client.get(
            "/api/v1/jobs?limit=600",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 422  # Validation error

    def test_pagination_skip_validation(self, client, auth_tokens):
        # Test negative skip
        resp = client.get(
            "/api/v1/jobs?skip=-1",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 422  # Validation error

    def test_empty_page(self, client, auth_tokens):
        resp = client.get(
            "/api/v1/jobs?skip=10000&limit=10",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["jobs"]) == 0
        assert data["skip"] == 10000


class TestJobListResponse:
    """Tests for job list response structure."""

    def test_response_structure(self, client, auth_tokens):
        resp = client.get(
            "/api/v1/jobs",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "jobs" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert isinstance(data["jobs"], list)
        assert isinstance(data["total"], int)

    def test_job_response_fields(self, client, auth_tokens, db):
        job = Job(
            external_id="test-external-id",
            title="Test Job",
            company="Test Company",
            location="Test Location",
            description="Test description",
            salary_min=100000,
            salary_max=150000,
            currency="USD",
            tags=["test", "python"],
            url="https://example.com/job",
            source="test",
        )
        db.add(job)
        db.commit()

        resp = client.get(
            "/api/v1/jobs?limit=1",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        
        if len(data["jobs"]) > 0:
            job_data = data["jobs"][0]
            assert "id" in job_data
            assert "external_id" in job_data
            assert "title" in job_data
            assert "company" in job_data
            assert "created_at" in job_data
            assert "updated_at" in job_data

    def test_unauthenticated_access(self, client):
        resp = client.get("/api/v1/jobs")
        assert resp.status_code == 401
