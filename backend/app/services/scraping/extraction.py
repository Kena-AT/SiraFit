"""Dependency-free extraction helpers shared across the import pipeline.

These helpers are used by both the Scrapling fetcher/parser
(``scrapling_fetcher.py``) and the import orchestration service
(``job_import.py``). Keeping them in a neutral module (importing only the
standard library) avoids a circular import between the two callers.
"""

import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse


# ─── URL Platform Detection ───────────────────────────────────────────────


def detect_platform(url: str) -> Optional[str]:
    """Return a stable platform key for a job URL, or None if unknown."""
    domain = urlparse(url).netloc.lower()
    if "linkedin" in domain:
        return "linkedin"
    if "indeed" in domain:
        return "indeed"
    if "glassdoor" in domain:
        return "glassdoor"
    if "ziprecruiter" in domain:
        return "ziprecruiter"
    if "simplyhired" in domain:
        return "simplyhired"
    if "lever.co" in domain:
        return "lever"
    if "greenhouse" in domain:
        return "greenhouse"
    if "ashbyhq" in domain or "ashby" in domain:
        return "ashby"
    if "workday" in domain:
        return "workday"
    return None


def extract_job_id_from_url(url: str) -> Optional[str]:
    """Extract a platform-specific job identifier from a URL, if present."""
    patterns = [
        r"linkedin\.com/jobs/view/(\d+)",
        r"indeed\.com/viewjob\?jk=([a-zA-Z0-9]+)",
        r"glassdoor\.com/job/listing/[^/]+-([a-zA-Z0-9]+)",
        r"ziprecruiter\.com/jobs/([^/]+)",
        r"simplyhired\.com/job/([^/]+)",
        r"lever\.co/[^/]+/([^/]+)",
        r"greenhouse\.io/[^/]+/jobs/(\d+)",
        r"ashbyhq\.com/[^/]+/jobs/(\d+)",
        r"workday\.com/[^/]+/job/(\d+)",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


# ─── URL Normalization ────────────────────────────────────────────────────


_TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "ref_src",
    "fbclid",
    "gclid",
}


def normalize_url(url: str) -> str:
    """Normalize a job URL for identity/deduplication purposes.

    Only transformations that preserve job identity are applied:
      - lowercase scheme and host
      - strip a leading ``www.``
      - strip a trailing slash
      - drop the fragment (``#...``)
      - drop known tracking query parameters (``utm_*`` / ``gclid`` / ``fbclid`` / ``ref``)

    The query string is otherwise preserved because some boards (e.g. Indeed)
    encode the job id in query parameters.
    """
    if not url:
        return url
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.rstrip("/") or "/"

    query_pairs: List[str] = []
    if parsed.query:
        for pair in parsed.query.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
            else:
                k, v = pair, ""
            if k.lower() in _TRACKING_PARAMS:
                continue
            query_pairs.append(f"{k}={v}")
    query = "&".join(query_pairs)

    return f"{scheme}://{netloc}{path}" + (f"?{query}" if query else "")


# ─── Salary Parsing ───────────────────────────────────────────────────────


def parse_salary_from_text(text: str) -> Tuple[Optional[int], Optional[int]]:
    """Return (salary_min, salary_max) parsed from free text, or (None, None).

    Handles hourly rates (annualized at 2080 hours), ``$120k``-style shorthand,
    and comma-separated ranges. Never fabricates a value that is not present.
    """
    if not text:
        return None, None

    # Hourly rate/range detection ($45/hr - $60/hr)
    hourly_match = re.search(
        r"\$(\d+(?:\.\d+)?)\s*(?:/|per)\s*(?:hr|hour)", text, re.IGNORECASE
    )
    if hourly_match:
        hourly_rate = float(hourly_match.group(1))
        annual = int(hourly_rate * 2080)
        return annual, annual

    k_pattern = r"\$(\d+(?:\.\d+)?)\s*[kK]\s*(?:-|–|to)\s*\$(\d+(?:\.\d+)?)\s*[kK]"
    m = re.search(k_pattern, text)
    if m:
        return int(float(m.group(1)) * 1000), int(float(m.group(2)) * 1000)

    single_k = r"\$(\d+(?:\.\d+)?)\s*[kK]"
    m_single = re.search(single_k, text)
    if m_single:
        return int(float(m_single.group(1)) * 1000), None

    nums = re.findall(r"\$?\s*(\d{2,3}(?:,\d{3})+|\d{4,6})", text)
    if len(nums) >= 2:
        try:
            return int(nums[0].replace(",", "")), int(nums[1].replace(",", ""))
        except ValueError:
            pass
    elif len(nums) == 1:
        try:
            return None, int(nums[0].replace(",", ""))
        except ValueError:
            pass
    return None, None


# ─── Tag Extraction ───────────────────────────────────────────────────────


SKILL_KEYWORDS = [
    "python",
    "javascript",
    "typescript",
    "go",
    "rust",
    "java",
    "c++",
    "c#",
    "react",
    "angular",
    "vue",
    "node",
    "nodejs",
    "django",
    "flask",
    "fastapi",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "aws",
    "gcp",
    "azure",
    "docker",
    "kubernetes",
    "terraform",
    "ci/cd",
    "git",
    "linux",
    "machine learning",
    "ai",
    "data science",
    "nlp",
    "computer vision",
    "rest api",
    "graphql",
    "grpc",
    "microservices",
    "distributed systems",
]


def extract_tags_from_text(text: str) -> List[str]:
    """Return known skill keywords found in free text."""
    if not text:
        return []
    text_lower = text.lower()
    return [skill for skill in SKILL_KEYWORDS if skill in text_lower]


# ─── HTML Cleanup ─────────────────────────────────────────────────────────


def _clean_html_to_text(html_fragment: str) -> str:
    """Strip HTML tags and collapse whitespace into plain text."""
    text = re.sub(r"<[^>]+>", " ", html_fragment or "")
    return re.sub(r"\s+", " ", text).strip()
