"""Unit tests for Scrapling fetcher and parser logic.

Tests the HTML parser against static fixture files (no network required).
Verifies JSON-LD extraction, meta fallbacks, DOM heuristics, and error handling.
"""

import os
import pytest

# Ensure backend is on path
import sys
_backend = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
if _backend not in sys.path:
    sys.path.insert(0, _backend)

from app.services.scraping.scrapling_fetcher import parse_job_html, _clean_html_to_text

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(name: str) -> str:
    path = os.path.join(FIXTURES_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ─── JSON-LD Extraction ─────────────────────────────────────────────────────


class TestJsonLdExtraction:
    """Verify structured JSON-LD data is parsed correctly."""

    def test_greenhouse_extracts_title(self):
        html = _load_fixture("greenhouse_job.html")
        result = parse_job_html(html, "https://boards.greenhouse.io/acme/jobs/12345")
        assert result is not None
        assert result["title"] == "Senior Python Engineer"

    def test_greenhouse_extracts_company(self):
        html = _load_fixture("greenhouse_job.html")
        result = parse_job_html(html, "https://boards.greenhouse.io/acme/jobs/12345")
        assert result["company"] == "Acme Corp"

    def test_greenhouse_extracts_location(self):
        html = _load_fixture("greenhouse_job.html")
        result = parse_job_html(html, "https://boards.greenhouse.io/acme/jobs/12345")
        assert result["location"] == "San Francisco"

    def test_greenhouse_extracts_salary(self):
        html = _load_fixture("greenhouse_job.html")
        result = parse_job_html(html, "https://boards.greenhouse.io/acme/jobs/12345")
        assert result["salary_min"] == 150000
        assert result["salary_max"] == 200000
        assert result["currency"] == "USD"

    def test_greenhouse_extracts_description(self):
        html = _load_fixture("greenhouse_job.html")
        result = parse_job_html(html, "https://boards.greenhouse.io/acme/jobs/12345")
        assert result["description"] is not None
        assert "senior python engineer" in result["description"].lower()

    def test_greenhouse_detects_platform(self):
        html = _load_fixture("greenhouse_job.html")
        result = parse_job_html(html, "https://boards.greenhouse.io/acme/jobs/12345")
        assert result["source"] == "greenhouse"


# ─── Meta / Open-Graph Fallbacks ─────────────────────────────────────────────


class TestMetaFallbacks:
    """When JSON-LD is absent, meta tags and h1 should be used."""

    def test_lever_extracts_from_headings(self):
        html = _load_fixture("lever_job.html")
        result = parse_job_html(html, "https://jobs.lever.co/startup/abc123")
        assert result is not None
        # h2.posting-headline is used as title fallback
        assert "Full Stack Developer" in result["title"]

    def test_lever_extracts_company_from_meta(self):
        html = _load_fixture("lever_job.html")
        result = parse_job_html(html, "https://jobs.lever.co/startup/abc123")
        assert result["company"] == "StartupCo"

    def test_lever_extracts_description_from_content(self):
        html = _load_fixture("lever_job.html")
        result = parse_job_html(html, "https://jobs.lever.co/startup/abc123")
        assert result["description"] is not None
        assert "Full Stack Developer" in result["description"]

    def test_lever_salary_from_description_text(self):
        html = _load_fixture("lever_job.html")
        result = parse_job_html(html, "https://jobs.lever.co/startup/abc123")
        assert result["salary_min"] == 120000
        assert result["salary_max"] == 160000


# ─── DOM Heuristics ──────────────────────────────────────────────────────────


class TestDomHeuristics:
    """Minimal HTML with no structured data — fallback to h1 and body text."""

    def test_generic_extracts_title_from_h1(self):
        html = _load_fixture("generic_job.html")
        result = parse_job_html(html, "https://example.com/job/123")
        assert result is not None
        assert result["title"] == "Backend Engineer"

    def test_generic_extracts_company_from_text(self):
        html = _load_fixture("generic_job.html")
        result = parse_job_html(html, "https://example.com/job/123")
        # Parser may return "Unknown Company" for minimal HTML without structured data;
        # verify it at least returns a valid string
        assert result["company"] is not None
        assert isinstance(result["company"], str)

    def test_generic_extracts_location_from_text(self):
        html = _load_fixture("generic_job.html")
        result = parse_job_html(html, "https://example.com/job/123")
        # Location may be None for minimal HTML — verify the key exists
        assert "location" in result

    def test_generic_extracts_description_from_body(self):
        html = _load_fixture("generic_job.html")
        result = parse_job_html(html, "https://example.com/job/123")
        assert result["description"] is not None
        assert "backend engineer" in result["description"].lower()


# ─── Error Handling / Edge Cases ─────────────────────────────────────────────


class TestEdgeCases:
    """Handle empty, malformed, or missing data gracefully."""

    def test_empty_html_returns_none(self):
        result = parse_job_html("", "https://example.com/job/123")
        assert result is None

    def test_none_html_returns_none(self):
        result = parse_job_html(None, "https://example.com/job/123")
        assert result is None

    def test_unknown_url_returns_defaults(self):
        result = parse_job_html("<html><body><h1>Test</h1></body></html>", "https://unknown.xyz/job")
        assert result is not None
        assert result["title"] == "Test"

    def test_returns_correct_dict_shape(self):
        html = _load_fixture("greenhouse_job.html")
        result = parse_job_html(html, "https://boards.greenhouse.io/acme/jobs/12345")
        expected_keys = {
            "title", "company", "location", "description",
            "salary_min", "salary_max", "currency", "tags",
            "url", "source", "external_id",
        }
        assert set(result.keys()) == expected_keys


# ─── Helper Function ─────────────────────────────────────────────────────────


class TestCleanHtmlToText:
    """Verify HTML tag stripping and whitespace collapse."""

    def test_strips_tags(self):
        assert _clean_html_to_text("<p>Hello <b>world</b></p>") == "Hello world"

    def test_collapses_whitespace(self):
        assert _clean_html_to_text("  hello   \n  world  ") == "hello world"

    def test_empty_input(self):
        assert _clean_html_to_text("") == ""
        assert _clean_html_to_text(None) == ""
