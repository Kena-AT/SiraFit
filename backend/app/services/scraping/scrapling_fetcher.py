"""Scrapling-based HTML fetcher and parser for job postings.

This is the **single source of truth** for fetch + parse logic. The import
orchestration service (``job_import.py``) imports ``fetch_job_html`` and
``parse_job_html`` from here — do not duplicate this logic there.

Fetching uses Scrapling's stealthy (curl_cffi) engine; no browser binaries are
required. To also use the adaptive browser fallback for JS-heavy boards, run
``scrapling install`` and configure ``Fetcher.configure(adaptive=True,
stealthy=True)`` instead.
"""

import json
import logging
import re
import uuid
from typing import Any, Dict, Optional

from app.services.scraping.extraction import (
    _clean_html_to_text,
    detect_platform,
    extract_job_id_from_url,
    extract_tags_from_text,
    normalize_url,
    parse_salary_from_text,
)

try:
    from scrapling import Fetcher, Selector

    _SCRAPLING_AVAILABLE = True
except Exception:  # pragma: no cover — optional dependency
    _SCRAPLING_AVAILABLE = False

logger = logging.getLogger(__name__)


# ─── Fetch error taxonomy ────────────────────────────────────────────────────
# Stable, bounded failure codes. The frontend maps these to friendly messages;
# logs retain the diagnostic category. Never expose raw exception text.


class FetchOutcome:
    """Result of a fetch attempt: either HTML or a stable error code."""

    __slots__ = ("html", "error_code")

    def __init__(self, html: Optional[str] = None, error_code: Optional[str] = None):
        self.html = html
        self.error_code = error_code


def _looks_empty_or_blocked(html: str) -> bool:
    """Heuristic for empty or anti-bot pages that should not be parsed."""
    if not html:
        return True
    # Visible text after stripping tags/whitespace.
    visible = "".join(re.split(r"\s+", _clean_html_to_text(html)))
    if len(visible) < 100:
        return True
    low = html.lower()
    return any(
        marker in low
        for marker in (
            "enable javascript",
            "cloudflare",
            "cf-chl",
            "captcha",
            "access denied",
        )
    )


def fetch_job_html_detailed(url: str, timeout: int = 15) -> FetchOutcome:
    """Fetch a job page and return a structured outcome (HTML or error code)."""
    if not _SCRAPLING_AVAILABLE:
        return FetchOutcome(None, "SCRAPLING_UNAVAILABLE")
    try:
        Fetcher.configure(stealthy=True)
        response = Fetcher.get(url, timeout=timeout, follow_redirects=True, retries=2)
    except Exception:
        return FetchOutcome(None, "FETCH_NETWORK_ERROR")
    if response is None:
        return FetchOutcome(None, "EMPTY_RESPONSE")
    body = getattr(response, "body", None)
    if not body:
        return FetchOutcome(None, "EMPTY_PAGE")
    html = body if isinstance(body, str) else body.decode("utf-8", "replace")
    if _looks_empty_or_blocked(html):
        return FetchOutcome(None, "ANTI_BOT_PAGE")
    return FetchOutcome(html, None)


def fetch_job_html(url: str, timeout: int = 15) -> Optional[str]:
    """Return raw HTML for a job page, or None on any failure.

    Backward-compatible wrapper around :func:`fetch_job_html_detailed`.
    """
    return fetch_job_html_detailed(url, timeout).html


# ─── Parse ───────────────────────────────────────────────────────────────────


def parse_job_html(html: str, url: str) -> Optional[Dict[str, Any]]:
    """Extract structured job fields from fetched HTML using Scrapling.

    Strategy: JSON-LD JobPosting → meta/Open-Graph tags → DOM heuristics.
    Returns the same dict shape as ``parse_job_from_url`` so the two merge
    cleanly. Returns ``None`` for empty/no HTML input.
    """
    if not html or not _SCRAPLING_AVAILABLE:
        return None

    clean_url = normalize_url(url)
    platform = detect_platform(clean_url)
    job_id = extract_job_id_from_url(clean_url)
    sel = Selector(html, adaptive=True, url=url)

    title = company = location = description = None
    salary_min = salary_max = None
    currency = "USD"

    # 1) JSON-LD JobPosting (many boards embed this structured data)
    try:
        for block in sel.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(block)
            except Exception:
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                if item.get("@type") not in ("JobPosting", ["JobPosting"]):
                    continue
                jp = item
                title = title or jp.get("title")
                org = jp.get("hiringOrganization")
                if isinstance(org, dict):
                    company = company or org.get("name")
                loc = jp.get("jobLocation")
                if isinstance(loc, dict):
                    addr = loc.get("address")
                    if isinstance(addr, dict):
                        location = location or (
                            addr.get("addressLocality") or addr.get("addressRegion")
                        )
                desc = jp.get("description")
                if desc and not description:
                    description = _clean_html_to_text(desc) if "<" in desc else desc
                bs = jp.get("baseSalary")
                if isinstance(bs, dict):
                    val = bs.get("value")
                    if isinstance(val, dict):
                        salary_min = salary_min or val.get("minValue")
                        salary_max = salary_max or val.get("maxValue")
                        currency = val.get("currency", currency)
                break
    except Exception:
        pass

    # 2) Meta / Open-Graph fallbacks
    if not title:
        title = (
            sel.css('meta[property="og:title"]::attr(content)').get()
            or sel.css("h1 ::text").get()
        )
    if not company:
        company = sel.css('meta[property="og:site_name"]::attr(content)').get()
    if not location:
        location = (
            sel.css('meta[property="og:locality"]::attr(content)').get()
            or sel.css('meta[property="og:region"]::attr(content)').get()
            or sel.css('meta[name="geo.placename"]::attr(content)').get()
            or sel.css('meta[property="og:locale"]::attr(content)').get()
        )

    # 3) Description: explicit job-description container, else body text
    if not description:
        parts = sel.css(
            "#job-description ::text, "
            "[class*='job-description'] ::text, "
            "[class*='description'] ::text"
        ).getall()
        if parts:
            description = " ".join(p.strip() for p in parts if p.strip())
    if not description:
        description = " ".join(sel.css("body ::text").getall())
    if description:
        description = _clean_html_to_text(description)

    # 4) Salary from free text when still missing
    if description and salary_min is None:
        salary_min, salary_max = parse_salary_from_text(description)

    tags = extract_tags_from_text(description or "")

    return {
        "title": title or "Unknown Position",
        "company": company or "Unknown Company",
        "location": location,
        "description": description,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "currency": currency,
        "tags": tags,
        "url": url,
        "source": platform or "url",
        "external_id": str(job_id or uuid.uuid4()),
    }
