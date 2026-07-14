"""
Tests for the job import system — service layer and API endpoints.
"""

import uuid


class TestImportService:
    """Direct tests of the import service functions."""

    def test_parse_job_from_url_linkedin(self):
        from app.services.job_import import parse_job_from_url

        url = "https://www.linkedin.com/jobs/view/1234567890"
        result = parse_job_from_url(url)
        assert result["source"] == "linkedin"
        assert result["external_id"] == "1234567890"
        assert "linkedin" in result["tags"]

    def test_parse_job_from_url_indeed(self):
        from app.services.job_import import parse_job_from_url

        url = "https://www.indeed.com/viewjob?jk=abc123def"
        result = parse_job_from_url(url)
        assert result["source"] == "indeed"
        assert result["external_id"] == "abc123def"

    def test_parse_job_from_url_unknown(self):
        from app.services.job_import import parse_job_from_url

        url = "https://example.com/jobs/some-position"
        result = parse_job_from_url(url)
        assert result["source"] == "url"
        assert result["title"] == "Some Position"

    def test_parse_job_from_description_basic(self):
        from app.services.job_import import parse_job_from_description

        desc = """Senior Software Engineer
        Company: Acme Corp
        Location: San Francisco, CA
        Salary: $150,000 - $200,000

        We are looking for a senior engineer with Python, React, and AWS experience.
        """
        result = parse_job_from_description(desc)
        assert "Senior" in result["title"]
        assert result["company"] == "Acme Corp"
        assert result["location"] == "San Francisco, CA"
        assert result["salary_min"] == 150000
        assert result["salary_max"] == 200000
        assert "python" in result["tags"]
        assert "react" in result["tags"]
        assert "aws" in result["tags"]

    def test_parse_job_from_description_short_fails(self):
        from app.services.job_import import parse_job_from_description

        desc = "Short text"
        result = parse_job_from_description(desc)
        assert result["title"] == "Unknown Position"

    def test_normalize_job(self):
        from app.services.job_import import normalize_job

        raw = {
            "title": "  senior engineer  ",
            "company": "at Acme Corp",
            "location": "  SF, CA  ",
            "description": "Python and React skills",
            "source": "description",
            "external_id": str(uuid.uuid4()),
        }
        result = normalize_job(raw)
        assert result["title"] == "Senior Engineer"
        assert result["company"] == "Acme Corp"
        assert result["location"] == "SF, CA"
        assert "python" in result["tags"]

    def test_check_duplicate_no_match(self, db, test_user):
        from app.services.job_import import check_duplicate

        job_data = {
            "title": "Software Engineer",
            "company": "Test Corp",
            "location": "Remote",
        }
        assert not check_duplicate(db, job_data)

    def test_check_duplicate_with_match(self, db, test_user):
        from app.services.job_import import check_duplicate
        from app.models.job import Job

        job = Job(
            external_id=str(uuid.uuid4()),
            title="Software Engineer",
            company="Test Corp",
            location="Remote",
        )
        db.add(job)
        db.commit()

        job_data = {
            "title": "Software Engineer",
            "company": "Test Corp",
            "location": "Remote",
        }
        assert check_duplicate(db, job_data)

    def test_detect_platform(self):
        from app.services.job_import import detect_platform

        assert detect_platform("https://linkedin.com/jobs/123") == "linkedin"
        assert detect_platform("https://indeed.com/viewjob") == "indeed"
        assert detect_platform("https://glassdoor.com/job") == "glassdoor"
        assert detect_platform("https://unknown.com/job") is None

    def test_extract_tags_from_text(self):
        from app.services.job_import import extract_tags_from_text

        text = "We use Python, React, and PostgreSQL in production."
        tags = extract_tags_from_text(text)
        assert "python" in tags
        assert "react" in tags
        assert "postgresql" in tags


class TestImportAPI:
    """Tests for the import API endpoints."""

    def test_import_url_unauthenticated(self, client):
        resp = client.post(
            "/api/v1/jobs/import",
            json={"source_type": "url", "data": "https://linkedin.com/jobs/view/123"},
        )
        assert resp.status_code == 401

    def test_import_url_success(self, client, auth_tokens):
        resp = client.post(
            "/api/v1/jobs/import",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={
                "source_type": "url",
                "data": "https://www.linkedin.com/jobs/view/123456",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "import_record" in data
        assert "jobs" in data
        assert "errors" in data
        assert data["import_record"]["status"] == "completed"
        assert data["import_record"]["source"] == "url"

    def test_import_description_success(self, client, auth_tokens):
        desc = """Backend Developer
        Company: DevCo
        Location: New York, NY
        Salary: $120,000 - $160,000

        We need a backend developer skilled in Python, PostgreSQL, and Docker.
        """
        resp = client.post(
            "/api/v1/jobs/import",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={"source_type": "description", "data": desc},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["import_record"]["status"] == "completed"
        assert len(data["jobs"]) == 1
        assert "Backend Developer" in data["jobs"][0]["title"]

    def test_import_description_too_short(self, client, auth_tokens):
        resp = client.post(
            "/api/v1/jobs/import",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={"source_type": "description", "data": "Too short"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["import_record"]["status"] == "failed"
        assert len(data["errors"]) > 0

    def test_import_history_unauthenticated(self, client):
        client.cookies.clear()
        resp = client.get("/api/v1/jobs/import/history")
        assert resp.status_code == 401

    def test_import_history_success(self, client, auth_tokens):
        resp = client.get(
            "/api/v1/jobs/import/history",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_import_history_with_records(self, client, auth_tokens):
        # First, import a job
        client.post(
            "/api/v1/jobs/import",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={"source_type": "url", "data": "https://linkedin.com/jobs/view/999"},
        )
        # Then check history
        resp = client.get(
            "/api/v1/jobs/import/history",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["source"] == "url"
        assert data[0]["status"] == "completed"

    def test_import_detail_not_found(self, client, auth_tokens):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/jobs/import/{fake_id}",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 404

    def test_import_duplicate_detection(self, client, auth_tokens):
        url = "https://linkedin.com/jobs/view/duplicate-test"
        # First import
        client.post(
            "/api/v1/jobs/import",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={"source_type": "url", "data": url},
        )
        # Second import of same URL
        resp = client.post(
            "/api/v1/jobs/import",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
            json={"source_type": "url", "data": url},
        )
        data = resp.json()
        assert data["import_record"]["status"] == "completed"
