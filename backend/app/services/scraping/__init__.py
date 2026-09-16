"""Scrapling-based job fetcher and parser.

Re-exports ``fetch_job_html`` and ``parse_job_html`` for use by
``services.job_import``. The actual implementation lives here to keep
job_import.py focused on the import pipeline rather than scraping internals.
"""

from app.services.scraping.scrapling_fetcher import (  # noqa: F401
    FetchOutcome,
    fetch_job_html,
    fetch_job_html_detailed,
    parse_job_html,
)
