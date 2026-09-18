import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

import requests

from app.services.scraping.extraction import normalize_url

logger = logging.getLogger(__name__)

SUPPORTED_PLATFORMS: Set[str] = {"linkedin", "indeed"}

PLATFORM_CONFIG: Dict[str, Dict[str, Any]] = {
    "linkedin": {
        "saved_jobs_url": "https://www.linkedin.com/my-items/saved-jobs/",
        "page_timeout_seconds": 30,
        "max_pages": 5,
        "max_jobs": 500,
        "login_indicators": [
            "/login",
            "/authwall",
            "/checkpoint/lg/login",
            "join-form",
            "session_password",
        ],
        "empty_indicators": [
            "No saved jobs",
            "You haven’t saved any jobs yet",
            "no-saved-jobs",
            "saved-items-empty",
        ],
        "structure_indicators": [
            "saved-jobs",
            "job-card",
            "reusable-search",
            "my-items",
            "entity-result",
        ],
    },
    "indeed": {
        "saved_jobs_url": "https://myjobs.indeed.com/saved",
        "page_timeout_seconds": 20,
        "max_pages": 10,
        "max_jobs": 500,
        "login_indicators": [
            "/account/login",
            "/auth",
            "/login",
            "signin_form",
            "login-submit",
        ],
        "empty_indicators": [
            "No saved jobs found",
            "You don't have any saved jobs",
            "empty-state",
        ],
        "structure_indicators": [
            "savedJobs",
            "job-card",
            "mosaic-provider-jobcards",
            "myjobs",
            "jobTitle",
        ],
    },
}

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


class SessionImporterError(Exception):
    """Base exception for session importer."""

    pass


class InvalidSessionConfig(SessionImporterError):
    """Raised when session configuration is missing or malformed."""

    pass


class SessionExpiredError(SessionImporterError):
    """Raised when the session is expired or authentication failed."""

    pass


class ScraperStructureError(SessionImporterError):
    """Raised when the platform page structure changed or is unrecognized."""

    pass


class ScraperFetchError(SessionImporterError):
    """Raised when a network or HTTP error occurs while fetching."""

    pass


class ScraperRateLimitError(SessionImporterError):
    """Raised when platform responds with 429 rate limit."""

    pass


@dataclass
class SavedJobReference:
    url: str
    external_id: Optional[str]
    title_hint: Optional[str] = None


class SavedJobsImporter:
    """Discovers saved-job URLs using authenticated user session."""

    def __init__(self, user_agent: Optional[str] = None):
        self.user_agent = user_agent or DEFAULT_USER_AGENT

    def _prepare_session(
        self, platform: str, session_data: Dict[str, Any]
    ) -> requests.Session:
        if platform not in SUPPORTED_PLATFORMS:
            raise InvalidSessionConfig(f"Platform '{platform}' is not supported")

        if not isinstance(session_data, dict):
            raise InvalidSessionConfig("Session data must be a dictionary")

        cookies = session_data.get("cookies")
        if not cookies or not isinstance(cookies, dict):
            raise InvalidSessionConfig("Missing or invalid cookies in session data")

        req_session = requests.Session()
        req_session.headers.update(
            {
                "User-Agent": session_data.get("user_agent") or self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

        if session_data.get("headers"):
            req_session.headers.update(session_data["headers"])

        for name, value in cookies.items():
            req_session.cookies.set(name, value)

        return req_session

    def validate_session(
        self, platform: str, session_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validate if the session is alive without scraping jobs."""
        if platform not in SUPPORTED_PLATFORMS:
            return False, f"Platform '{platform}' is not supported"

        cfg = PLATFORM_CONFIG[platform]
        try:
            session = self._prepare_session(platform, session_data)
            url = cfg["saved_jobs_url"]
            resp = session.get(
                url, timeout=cfg["page_timeout_seconds"], allow_redirects=True
            )

            if resp.status_code in (401, 403):
                return False, "Session authentication failed (HTTP 401/403)"

            # Check redirect URL and body for login indicators
            for ind in cfg["login_indicators"]:
                if ind in resp.url.lower() or ind in resp.text.lower():
                    return False, "Session has expired or redirected to login"

            if resp.status_code >= 400:
                return False, f"Platform returned HTTP {resp.status_code}"

            return True, "Session is valid"
        except Exception as exc:
            logger.warning(
                "session_validation_error",
                extra={"platform": platform, "error": str(exc)},
            )
            return False, "Session validation request failed (network error or timeout)"

    def fetch_saved_jobs_list(
        self,
        platform: str,
        session_data: Dict[str, Any],
    ) -> Tuple[List[SavedJobReference], str]:
        """Fetch and extract saved job URLs.

        Returns:
            Tuple[List[SavedJobReference], status_str] where status_str is
            "completed" or "completed_empty".
        """
        if platform not in SUPPORTED_PLATFORMS:
            raise InvalidSessionConfig(f"Platform '{platform}' is not supported")

        cfg = PLATFORM_CONFIG[platform]
        session = self._prepare_session(platform, session_data)

        references: List[SavedJobReference] = []
        seen_ids: Set[str] = set()

        url = cfg["saved_jobs_url"]
        page = 1
        has_empty_signal = False

        while url and page <= cfg["max_pages"] and len(references) < cfg["max_jobs"]:
            try:
                resp = session.get(
                    url, timeout=cfg["page_timeout_seconds"], allow_redirects=True
                )
            except Exception as exc:
                raise ScraperFetchError(f"Network error fetching saved jobs: {exc}")

            if resp.status_code in (401, 403):
                raise SessionExpiredError(
                    "Session expired or authentication failed (HTTP 401/403)"
                )

            for ind in cfg["login_indicators"]:
                if ind in resp.url.lower() or ind in resp.text.lower():
                    raise SessionExpiredError("Session expired (redirected to login)")

            if resp.status_code >= 400:
                raise ScraperFetchError(f"Platform returned HTTP {resp.status_code}")

            html = resp.text

            # Check for structural signals
            has_structure = any(
                ind.lower() in html.lower() for ind in cfg["structure_indicators"]
            )
            has_empty = any(
                ind.lower() in html.lower() for ind in cfg["empty_indicators"]
            )

            if has_empty:
                has_empty_signal = True

            # Extract platform specific jobs
            page_refs, next_url = self._parse_platform_saved_jobs(
                platform, html, resp.url
            )

            if not page_refs and not has_structure and not has_empty:
                # Neither job cards nor recognized structure nor empty state found
                raise ScraperStructureError(
                    f"Platform page structure unrecognized for {platform}; possible anti-bot or structural change"
                )

            for ref in page_refs:
                dedup_key = ref.external_id or ref.url
                if dedup_key not in seen_ids:
                    seen_ids.add(dedup_key)
                    references.append(ref)
                    if len(references) >= cfg["max_jobs"]:
                        break

            url = next_url
            page += 1

        if not references:
            if has_empty_signal:
                return [], "completed_empty"
            return [], "completed_empty"

        return references, "completed"

    def _parse_platform_saved_jobs(
        self,
        platform: str,
        html: str,
        base_url: str,
    ) -> Tuple[List[SavedJobReference], Optional[str]]:
        """Extract job references and optional next page URL from HTML."""
        if platform == "linkedin":
            return self._parse_linkedin_saved_jobs(html, base_url)
        elif platform == "indeed":
            return self._parse_indeed_saved_jobs(html, base_url)
        return [], None

    def _parse_linkedin_saved_jobs(
        self,
        html: str,
        base_url: str,
    ) -> Tuple[List[SavedJobReference], Optional[str]]:
        refs: List[SavedJobReference] = []

        # Find URLs matching /jobs/view/<job_id>
        # Pattern 1: /jobs/view/1234567890/
        matches = re.findall(r'href="([^"]*?/jobs/view/(\d+)[^"]*?)"', html)
        for href, job_id in matches:
            clean_url = normalize_url(urljoin(base_url, href))
            refs.append(
                SavedJobReference(
                    url=clean_url,
                    external_id=f"linkedin:{job_id}",
                )
            )

        # Pattern 2: urn:li:fsd_jobPosting:1234567890
        urn_matches = re.findall(r"urn:li:fsd_jobPosting:(\d+)", html)
        for job_id in urn_matches:
            if not any(r.external_id == f"linkedin:{job_id}" for r in refs):
                job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
                refs.append(
                    SavedJobReference(
                        url=job_url,
                        external_id=f"linkedin:{job_id}",
                    )
                )

        # Pattern 3: currentJobId=1234567890
        param_matches = re.findall(r"currentJobId=(\d+)", html)
        for job_id in param_matches:
            if not any(r.external_id == f"linkedin:{job_id}" for r in refs):
                job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
                refs.append(
                    SavedJobReference(
                        url=job_url,
                        external_id=f"linkedin:{job_id}",
                    )
                )

        # Pagination detection (e.g. start=25 or next link)
        next_url = None
        next_match = re.search(
            r'href="([^"]*?[?&]start=\d+[^"]*?)"[^>]*?aria-label="Next"', html
        )
        if next_match:
            next_url = urljoin(base_url, next_match.group(1))

        return refs, next_url

    def _parse_indeed_saved_jobs(
        self,
        html: str,
        base_url: str,
    ) -> Tuple[List[SavedJobReference], Optional[str]]:
        refs: List[SavedJobReference] = []

        # Find URLs matching jk=<job_key> or /rc/clk?jk=<job_key>
        matches = re.findall(
            r'href="([^"]*?(?:jk=|/viewjob\?jk=)([a-zA-Z0-9_-]+)[^"]*?)"', html
        )
        for href, job_key in matches:
            clean_url = normalize_url(urljoin(base_url, href))
            refs.append(
                SavedJobReference(
                    url=clean_url,
                    external_id=f"indeed:{job_key}",
                )
            )

        # Pattern 2: data-jk="<job_key>"
        data_jk_matches = re.findall(r'data-jk="([a-zA-Z0-9_-]+)"', html)
        for job_key in data_jk_matches:
            if not any(r.external_id == f"indeed:{job_key}" for r in refs):
                job_url = f"https://www.indeed.com/viewjob?jk={job_key}"
                refs.append(
                    SavedJobReference(
                        url=job_url,
                        external_id=f"indeed:{job_key}",
                    )
                )

        next_url = None
        next_match = re.search(
            r'href="([^"]*?[?&]start=\d+[^"]*?)"[^>]*?data-testid="pagination-page-next"',
            html,
        )
        if next_match:
            next_url = urljoin(base_url, next_match.group(1))

        return refs, next_url
