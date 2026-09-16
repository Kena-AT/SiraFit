"""Adaptive selector definitions for each job board platform.

Selectors are CSS paths used by Scrapling's ``Selector(adaptive=True)`` which
auto-relocates elements when the page layout changes. Each platform may have
slightly different DOM structures; these selectors cover the most common
layouts as of 2026-09.

The ``PLATFORM_PATTERNS`` dict maps domain substrings to platform keys for
``_detect_platform()`` in job_import.py.
"""

from typing import Dict, List

# ─── Domain → Platform Mapping ──────────────────────────────────────────────

PLATFORM_PATTERNS: Dict[str, List[str]] = {
    "linkedin":    ["linkedin.com"],
    "indeed":      ["indeed.com"],
    "glassdoor":   ["glassdoor.com"],
    "ziprecruiter":["ziprecruiter.com"],
    "simplyhired": ["simplyhired.com"],
    "lever":       ["lever.co"],
    "greenhouse":  ["greenhouse.io", "boards.greenhouse.io"],
    "ashby":       ["ashbyhq.com", "jobs.ashbyhq.com"],
    "workday":     ["myworkdayjobs.com", "workday.com"],
}

# ─── Per-Platform CSS Selectors ─────────────────────────────────────────────
# Each value is a dict of field → CSS selector string.  When using
# ``Selector(adaptive=True)``, these will auto-relocate to the nearest
# semantic match if the original element is missing.

PLATFORM_SELECTORS: Dict[str, Dict[str, str]] = {
    "linkedin": {
        "title":       "h1.text-heading-xlarge",
        "company":     "a[href*='/company/'] span",
        "location":    "span.jobs-unified-top-card__list span:first-child",
        "description": "div#job-details div.description",
        "salary":      "li[data-test-matcher='salary'] span",
    },
    "greenhouse": {
        "title":       "h1.job-title",
        "company":     ".company-name",
        "location":    ".location",
        "description": "#content",
        "salary":      ".salary",
    },
    "lever": {
        "title":       "h2.posting-headline",
        "company":     ".posting-headline .company-name",
        "location":    ".posting-headline .location",
        "description": ".posting-page .content",
        "salary":      ".salary",
    },
    "indeed": {
        "title":       "h1.jobsearch-JobInfoHeader-title",
        "company":     "div[data-testid='inlineHeader-companyName'] a",
        "location":    "div[data-testid='inlineHeader-companyLocation']",
        "description": "#jobDescriptionText",
        "salary":      "div[data-testid='attribute_snippet']",
    },
    "glassdoor": {
        "title":       "h1[data-test='job-title']",
        "company":     "div.strong-600",
        "location":    "div.job-details-flex__labels",
        "description": "#JobDescriptionContainer",
        "salary":      ".salaryList__item",
    },
    "ashby": {
        "title":       "h1",
        "company":     ".ashby-job-posting-header h2",
        "location":    ".ashby-job-posting-badges span",
        "description": ".ashby-job-posting-page-section",
        "salary":      ".ashby-job-posting-badges",
    },
    "workday": {
        "title":       "[data-automation-id='jobTitle']",
        "company":     "[data-automation-id='companyName']",
        "location":    "[data-automation-id='locationText']",
        "description": "[data-automation-id='jobPostingDescription']",
        "salary":      "[data-automation-id='salary']",
    },
}

# ─── Generic / Fallback Selectors ────────────────────────────────────────────

GENERIC_SELECTORS: Dict[str, str] = {
    "title":       "h1",
    "company":     "meta[property='og:site_name']::attr(content)",
    "location":    "meta[property='og:locale']::attr(content)",
    "description": (
        "#job-description ::text, "
        "[class*='job-description'] ::text, "
        "[class*='description'] ::text"
    ),
}
