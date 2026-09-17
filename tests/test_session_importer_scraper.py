"""
Tests for SavedJobsImporter (Sprint 5).

Verifies validation, job discovery, and error handling
for LinkedIn and Indeed saved-jobs workflows with mock HTTP responses.
"""

from unittest.mock import patch, MagicMock
import pytest

from app.services.scraping.session_importer import (
    SavedJobsImporter,
    SessionExpiredError,
    ScraperStructureError,
    ScraperFetchError,
    ScraperRateLimitError,
    SUPPORTED_PLATFORMS,
)


SAMPLE_LINKEDIN_SAVED_JOBS_HTML = """
<!DOCTYPE html>
<html>
<body>
  <div class="scaffold-layout__list-item" data-chameleon-result-urn="urn:li:jobPosting:123456789">
    <div class="entity-result__item">
      <a class="job-card-list__title--link" href="https://www.linkedin.com/jobs/view/123456789/">Senior Backend Engineer</a>
      <span class="job-card-container__primary-description">Acme Corp</span>
    </div>
  </div>
  <div class="scaffold-layout__list-item" data-chameleon-result-urn="urn:li:jobPosting:987654321">
    <div class="entity-result__item">
      <a class="job-card-list__title--link" href="https://www.linkedin.com/jobs/view/987654321/">Full Stack Developer</a>
    </div>
  </div>
</body>
</html>
"""

SAMPLE_INDEED_SAVED_JOBS_HTML = """
<!DOCTYPE html>
<html>
<body>
  <div class="jobsearch-SavedJobs-card">
    <a class="jobsearch-SavedJobs-title" href="https://www.indeed.com/viewjob?jk=indeed_job_abc123">Python Tech Lead</a>
  </div>
</body>
</html>
"""


def test_supported_platforms_registry():
    """Verify supported platforms registry."""
    assert "linkedin" in SUPPORTED_PLATFORMS
    assert "indeed" in SUPPORTED_PLATFORMS


def test_validate_session_success():
    """Verify session validation returns valid=True when response is OK."""
    importer = SavedJobsImporter()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://www.linkedin.com/my-items/saved-jobs/"
    mock_resp.text = SAMPLE_LINKEDIN_SAVED_JOBS_HTML

    with patch("requests.Session.get", return_value=mock_resp):
        valid, msg = importer.validate_session("linkedin", {"cookies": {"li_at": "valid_token"}})
        assert valid is True
        assert "valid" in msg.lower()


def test_validate_session_expired_redirect_to_login():
    """Verify session validation returns valid=False when redirected to login."""
    importer = SavedJobsImporter()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://www.linkedin.com/login?from=saved_jobs"
    mock_resp.text = "<html><body>Please sign in</body></html>"

    with patch("requests.Session.get", return_value=mock_resp):
        valid, msg = importer.validate_session("linkedin", {"cookies": {"li_at": "expired_token"}})
        assert valid is False
        assert "expired" in msg.lower() or "login" in msg.lower()


def test_validate_session_unauthorized_status():
    """Verify session validation returns valid=False on 401 or 403."""
    importer = SavedJobsImporter()

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.url = "https://myjobs.indeed.com/saved"
    mock_resp.text = "Unauthorized"

    with patch("requests.Session.get", return_value=mock_resp):
        valid, msg = importer.validate_session("indeed", {"cookies": {"CTK": "bad_token"}})
        assert valid is False


def test_fetch_saved_jobs_list_linkedin():
    """Verify discovering LinkedIn saved jobs extracts cards with external_ids."""
    importer = SavedJobsImporter()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://www.linkedin.com/my-items/saved-jobs/"
    mock_resp.text = SAMPLE_LINKEDIN_SAVED_JOBS_HTML

    with patch("requests.Session.get", return_value=mock_resp):
        refs, status = importer.fetch_saved_jobs_list("linkedin", {"cookies": {"li_at": "valid_token"}})

    assert status == "completed"
    assert len(refs) == 2
    assert refs[0].external_id == "linkedin:123456789"
    assert "123456789" in refs[0].url

    assert refs[1].external_id == "linkedin:987654321"


def test_fetch_saved_jobs_list_indeed():
    """Verify discovering Indeed saved jobs extracts cards with external_ids."""
    importer = SavedJobsImporter()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://myjobs.indeed.com/saved"
    mock_resp.text = SAMPLE_INDEED_SAVED_JOBS_HTML

    with patch("requests.Session.get", return_value=mock_resp):
        refs, status = importer.fetch_saved_jobs_list("indeed", {"cookies": {"CTK": "valid_token"}})

    assert status == "completed"
    assert len(refs) == 1
    assert refs[0].external_id == "indeed:indeed_job_abc123"


def test_fetch_saved_jobs_list_empty_feed():
    """Verify empty feed returns empty list without error."""
    importer = SavedJobsImporter()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://www.linkedin.com/my-items/saved-jobs/"
    mock_resp.text = "<html><body><div class='saved-jobs'>No saved jobs</div></body></html>"

    with patch("requests.Session.get", return_value=mock_resp):
        refs, status = importer.fetch_saved_jobs_list("linkedin", {"cookies": {"li_at": "valid_token"}})

    assert refs == []
    assert status == "completed_empty"


def test_fetch_saved_jobs_list_expired_raises():
    """Verify discovery raises SessionExpiredError if redirected to login."""
    importer = SavedJobsImporter()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://www.linkedin.com/checkpoint/lg/login"
    mock_resp.text = "Login page"

    with patch("requests.Session.get", return_value=mock_resp):
        with pytest.raises(SessionExpiredError):
            importer.fetch_saved_jobs_list("linkedin", {"cookies": {"li_at": "expired_token"}})


def test_fetch_saved_jobs_list_unrecognized_structure_raises():
    """Verify discovery raises ScraperStructureError if page structure is unrecognized."""
    importer = SavedJobsImporter()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://www.linkedin.com/my-items/saved-jobs/"
    mock_resp.text = "<html><body>Something completely unrelated</body></html>"

    with patch("requests.Session.get", return_value=mock_resp):
        with pytest.raises(ScraperStructureError):
            importer.fetch_saved_jobs_list("linkedin", {"cookies": {"li_at": "token"}})
