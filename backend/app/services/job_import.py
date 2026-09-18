import re
import uuid
import csv
import io
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)
from app.core import metrics
from app.models.job import Job, JobImport, JobImportItem
from app.models.scrape_history import ScrapeHistory
from app.services.scraping.extraction import (
    detect_platform,
    extract_job_id_from_url,
    extract_tags_from_text,
    normalize_url,
)
from app.services.scraping.scrapling_fetcher import fetch_job_html, parse_job_html


# ─── URL Parsing ──────────────────────────────────────────────────────────


def parse_job_from_url(url: str) -> Dict[str, Any]:
    """Heuristic parser: derive limited fields from the URL alone.

    Used when Scrapling is unavailable or fetching fails. Never fabricates
    fields that were not actually found.
    """
    clean_url = normalize_url(url)
    platform = detect_platform(clean_url)
    job_id = extract_job_id_from_url(clean_url)

    company = "Unknown Source"
    parsed_url = urlparse(url)
    path_segments = [s for s in parsed_url.path.strip("/").split("/") if s]

    if platform in ("lever", "greenhouse", "ashby") and len(path_segments) > 0:
        company = path_segments[0].replace("-", " ").title()
    elif platform:
        company_hints = {
            "linkedin": "LinkedIn",
            "indeed": "Indeed",
            "glassdoor": "Glassdoor",
            "ziprecruiter": "ZipRecruiter",
            "simplyhired": "SimplyHired",
            "workday": "Workday",
        }
        company = company_hints.get(platform, platform.title())
    else:
        hostname = parsed_url.hostname or ""
        parts = [
            p
            for p in hostname.split(".")
            if p not in ("www", "com", "io", "co", "org", "net", "gov", "edu")
        ]
        if parts:
            company = parts[0].title()

    title = "Unknown Position"
    for seg in reversed(path_segments):
        seg_clean = seg.replace("-", " ").replace("_", " ").title()
        if seg_clean and seg_clean.lower() not in (
            "jobs",
            "job",
            "view",
            "listing",
            "apply",
        ):
            title = seg_clean
            break

    description = f"Job listing for {title} at {company}. Imported from URL: {url}"

    return {
        "title": title,
        "company": company,
        "location": None,
        "description": description,
        "salary_min": None,
        "salary_max": None,
        "currency": "USD",
        "tags": [platform] if platform else [],
        "url": url,
        "source": platform or "url",
        "external_id": str(job_id or uuid.uuid4()),
    }


# ─── Description Parsing ──────────────────────────────────────────────────

SENIORITY_KEYWORDS = [
    "senior",
    "staff",
    "principal",
    "lead",
    "junior",
    "mid",
    "associate",
    "intern",
    "graduate",
    "entry",
    "experienced",
]


def extract_field_from_text(
    text: str, field: str, keywords: List[str]
) -> Optional[str]:
    lines = text.split("\n")
    for line in lines:
        line_lower = line.lower().strip()
        for kw in keywords:
            if kw in line_lower:
                colon_idx = line.find(":")
                if colon_idx == -1:
                    colon_idx = line.find("-")
                if colon_idx != -1 and colon_idx < len(line) - 1:
                    value = line[colon_idx + 1 :].strip()
                    if value:
                        return value
    return None


TITLE_KEYWORDS = [
    "engineer",
    "developer",
    "scientist",
    "architect",
    "manager",
    "designer",
    "analyst",
    "intern",
    "specialist",
    "consultant",
]


def parse_job_from_description(description: str) -> Dict[str, Any]:
    lines = [line.strip() for line in description.split("\n") if line.strip()]

    title = "Unknown Position"
    if lines:
        first_line = lines[0]
        if any(kw in first_line.lower() for kw in TITLE_KEYWORDS):
            title = first_line

    company = extract_field_from_text(
        description,
        "company",
        [
            "company",
            "organization",
            "employer",
            "at ",
        ],
    )

    location = extract_field_from_text(
        description,
        "location",
        [
            "location",
            "office",
            "site",
            "where",
        ],
    )

    salary_text = extract_field_from_text(
        description,
        "salary",
        [
            "salary",
            "compensation",
            "pay",
            "range",
        ],
    )
    salary_min, salary_max = None, None
    if salary_text:
        nums = re.findall(r"\d[\d,]*", salary_text.replace(",", ""))
        if len(nums) >= 2:
            salary_min = int(nums[0].replace(",", ""))
            salary_max = int(nums[1].replace(",", ""))
        elif len(nums) == 1:
            salary_max = int(nums[0].replace(",", ""))

    tags = extract_tags_from_text(description)

    return {
        "title": title,
        "company": company or "Unknown Company",
        "location": location,
        "description": description,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "currency": "USD",
        "tags": tags,
        "url": None,
        "source": "description",
        "external_id": str(uuid.uuid4()),
    }


def parse_job_csv(csv_content: str) -> List[Dict[str, Any]]:
    jobs = []
    try:
        f = io.StringIO(csv_content.strip())
        sample = f.read(2048)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
            reader = csv.DictReader(f, dialect=dialect)
        except Exception:
            f.seek(0)
            reader = csv.DictReader(f)

        if reader.fieldnames:
            fieldnames_lower = [fn.lower().strip() for fn in reader.fieldnames]
            has_url_col = any("url" in fn or "link" in fn for fn in fieldnames_lower)
            has_title_col = any("title" in fn for fn in fieldnames_lower)

            if not has_url_col and not has_title_col and len(reader.fieldnames) == 1:
                f.seek(0)
                for line in f:
                    line = line.strip()
                    if (
                        line
                        and not line.lower().startswith("url")
                        and not line.lower().startswith("link")
                    ):
                        if line.startswith("http://") or line.startswith("https://"):
                            jobs.append(parse_job_from_url(line))
                        else:
                            jobs.append(parse_job_from_description(line))
                return jobs

            for row in reader:
                row_lower = {k.lower().strip(): v for k, v in row.items() if k}
                url = (
                    row_lower.get("url")
                    or row_lower.get("link")
                    or row_lower.get("job_url")
                )
                title = (
                    row_lower.get("title")
                    or row_lower.get("job_title")
                    or row_lower.get("position")
                )
                company = (
                    row_lower.get("company")
                    or row_lower.get("employer")
                    or row_lower.get("organization")
                )
                location = (
                    row_lower.get("location")
                    or row_lower.get("place")
                    or row_lower.get("office")
                )
                description = (
                    row_lower.get("description")
                    or row_lower.get("desc")
                    or row_lower.get("details")
                )

                if url and not title:
                    parsed_url_job = parse_job_from_url(url)
                    if company:
                        parsed_url_job["company"] = company
                    if location:
                        parsed_url_job["location"] = location
                    jobs.append(parsed_url_job)
                elif title or description:
                    jobs.append(
                        {
                            "title": title or "Unknown Position",
                            "company": company or "Unknown Company",
                            "location": location,
                            "description": description
                            or (
                                f"Position: {title} at {company}"
                                if title and company
                                else "Imported from CSV"
                            ),
                            "salary_min": None,
                            "salary_max": None,
                            "currency": "USD",
                            "tags": extract_tags_from_text(description or title or ""),
                            "url": url,
                            "source": "csv",
                            "external_id": str(uuid.uuid4()),
                        }
                    )
                elif url:
                    jobs.append(parse_job_from_url(url))
        else:
            f.seek(0)
            for line in f:
                line = line.strip()
                if line:
                    if line.startswith("http://") or line.startswith("https://"):
                        jobs.append(parse_job_from_url(line))
                    else:
                        jobs.append(parse_job_from_description(line))
    except Exception:
        for line in csv_content.split("\n"):
            line = line.strip()
            if line:
                if line.startswith("http://") or line.startswith("https://"):
                    jobs.append(parse_job_from_url(line))
                else:
                    try:
                        jobs.append(parse_job_from_description(line))
                    except Exception:
                        pass
    return jobs


# ─── Normalization Pipeline ────────────────────────────────────────────────


def normalize_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(job_data)

    if normalized.get("title"):
        normalized["title"] = normalized["title"].strip().title()
        normalized["title"] = re.sub(r"\s+", " ", normalized["title"])

    if normalized.get("company"):
        normalized["company"] = normalized["company"].strip()
        if normalized["company"].lower().startswith("at "):
            normalized["company"] = normalized["company"][3:].strip()

    if normalized.get("location"):
        normalized["location"] = normalized["location"].strip()
        normalized["location"] = re.sub(r"\s+", " ", normalized["location"])

    if not normalized.get("tags"):
        desc = normalized.get("description", "")
        if desc:
            normalized["tags"] = extract_tags_from_text(desc)
        else:
            normalized["tags"] = []

    normalized["tags"] = list(set(t.lower() for t in normalized.get("tags", [])))

    return normalized


# ─── Deduplication ─────────────────────────────────────────────────────────


def normalize_for_dedup(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower().strip())


def check_duplicate(db: Session, job_data: Dict[str, Any]) -> Optional[Job]:
    """Check if a job already exists.

    Returns the matched :class:`Job` instance (or ``None``), so callers can
    link the import item to the pre-existing job.

    Identity resolution order:
      1. Exact ``external_id`` match (stable URL-derived identity).
      2. Fuzzy title + company + location match (fallback for parity with
         legacy imports and heuristic-only data).
    """
    external_id = job_data.get("external_id")
    if external_id:
        existing = db.query(Job).filter(Job.external_id == external_id).first()
        if existing:
            return existing

    title = job_data.get("title", "")
    company = job_data.get("company", "")
    location = job_data.get("location", "") or ""

    query = db.query(Job)

    if title:
        query = query.filter(Job.title.ilike(f"%{title}%"))

    if company:
        query = query.filter(Job.company.ilike(f"%{company}%"))

    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    return query.limit(1).first()


# ─── Main Import Pipeline ─────────────────────────────────────────────────


def process_import(
    db: Session,
    user_id: uuid.UUID,
    source_type: str,
    data: str,
    existing_job_import: Optional[JobImport] = None,
) -> Tuple[JobImport, List[Dict[str, Any]], List[str], Dict[str, Any]]:
    """Run the import pipeline for a single job source.

    If ``existing_job_import`` is supplied, the pipeline runs against that
    already-persisted record (the async/worker path) instead of creating a new
    one — this keeps a single authoritative import pipeline.

    Returns:
        (job_import, jobs_data, errors, scrape_meta) where scrape_meta contains
        method_used, duration_ms, fields_extracted, and source_platform for URL
        imports (empty dict for description/csv sources).
    """
    if existing_job_import is not None:
        job_import = existing_job_import
        job_import.status = "processing"
    else:
        job_import = JobImport(
            user_id=user_id,
            source=source_type,
            status="processing",
            source_data=data[:2000],
        )
        db.add(job_import)
    db.commit()
    db.refresh(job_import)

    errors = []
    jobs_data = []
    scrape_meta: Dict[str, Any] = {}

    metrics.JOB_IMPORTS_TOTAL.labels(source_type).inc()

    try:
        parsed_list = []
        if source_type == "url":
            parsed = parse_job_from_url(data)
            # ── Enrichment-first: try scraping, fall back to heuristic ──────
            start = time.monotonic()
            method = "heuristic"
            platform = detect_platform(data)
            try:
                html = fetch_job_html(data)
            except Exception:
                html = None

            metrics.SCRAPE_ATTEMPTS.labels(platform or "unknown", "url").inc()

            if html:
                try:
                    enriched = parse_job_html(html, data)
                except Exception:
                    enriched = None
                if enriched:
                    for key in (
                        "title",
                        "company",
                        "location",
                        "description",
                        "salary_min",
                        "salary_max",
                        "currency",
                        "tags",
                    ):
                        # Only override when the enriched value is not None.
                        # This prevents a zero-value or empty-string from the
                        # scraper from silently replacing the heuristic parser's
                        # result (which may be None or a valid non-zero value).
                        if enriched.get(key) is not None:
                            parsed[key] = enriched[key]
                    method = "scrapling"

            if method == "scrapling":
                metrics.SCRAPE_SUCCESS.labels(platform or "unknown", "scrapling").inc()
            else:
                metrics.SCRAPE_PARTIAL.labels(platform or "unknown").inc()

            duration_ms = int((time.monotonic() - start) * 1000)
            fields_count = len([v for v in parsed.values() if v])

            scrape_meta = {
                "method_used": method,
                "duration_ms": duration_ms,
                "fields_extracted": fields_count,
                "source_platform": platform,
            }

            # ── Log to ScrapeHistory ─────────────────────────────────────────
            try:
                db.add(
                    ScrapeHistory(
                        user_id=user_id,
                        url=data,
                        source_platform=platform,
                        method_used=method,
                        success="true" if method == "scrapling" else "partial",
                        fields_extracted=fields_count,
                        duration_ms=duration_ms,
                    )
                )
                db.commit()
            except Exception:
                # Never let logging failure break the import
                db.rollback()

            parsed_list.append(parsed)
        elif source_type == "description":
            if len(data.strip()) < 100:
                raise ValueError("Description must be at least 100 characters")
            parsed_list.append(parse_job_from_description(data))
        elif source_type == "csv":
            if not data.strip():
                raise ValueError("CSV data cannot be empty")
            parsed_list = parse_job_csv(data)
            if not parsed_list:
                raise ValueError("No valid jobs found in CSV")
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

        for parsed in parsed_list:
            normalized = normalize_job(parsed)

            existing_job = check_duplicate(db, normalized)

            if existing_job:
                job_import.fail_count += 1
                metrics.JOB_IMPORTS_DUPLICATE.inc()
                errors.append(
                    f"Duplicate job: {normalized['title']} at {normalized['company']}"
                )
                db.add(
                    JobImportItem(
                        import_id=job_import.id,
                        job_id=existing_job.id,
                        status="duplicate",
                        title_guess=normalized["title"],
                    )
                )
            else:
                job = Job(
                    external_id=normalized["external_id"],
                    title=normalized["title"],
                    company=normalized["company"],
                    location=normalized.get("location"),
                    description=normalized.get("description"),
                    salary_min=normalized.get("salary_min"),
                    salary_max=normalized.get("salary_max"),
                    currency=normalized.get("currency"),
                    tags=normalized.get("tags", []),
                    url=normalized.get("url"),
                    source=normalized.get("source", source_type),
                    import_id=job_import.id,
                )
                db.add(job)
                db.commit()
                db.refresh(job)
                job_import.ok_count += 1
                normalized["id"] = str(job.id)
                normalized["import_status"] = "imported"
                jobs_data.append(normalized)
                db.add(
                    JobImportItem(
                        import_id=job_import.id,
                        job_id=job.id,
                        status="imported",
                        title_guess=normalized["title"],
                    )
                )
                # Trigger async embedding generation (Sprint 8)
                try:
                    from app.worker.tasks.embeddings import enqueue_job_embedding

                    enqueue_job_embedding(job.id)
                except Exception as emb_err:
                    logger.warning(
                        "Failed to enqueue embedding for job %s: %s", job.id, emb_err
                    )

        job_import.total_found = job_import.ok_count + job_import.fail_count
        job_import.status = "completed"
        job_import.errors = errors

        # Mark partial if heuristic-only URL imports had no real description
        if source_type == "url" and scrape_meta.get("method_used") == "heuristic":
            has_real_desc = any(
                j.get("description")
                and "Imported from URL:" not in j.get("description")
                for j in jobs_data
            )
            if not has_real_desc:
                job_import.partial = True

    except Exception as e:
        job_import.status = "failed"
        job_import.fail_count += 1
        metrics.JOB_IMPORTS_FAILED.inc()
        errors.append(str(e))
        job_import.errors = errors
        title_guess = None
        if parsed_list and isinstance(parsed_list[0], dict):
            title_guess = parsed_list[0].get("title")
        db.add(
            JobImportItem(
                import_id=job_import.id,
                job_id=None,
                status="failed",
                error_message=str(e),
                title_guess=title_guess,
            )
        )

    db.commit()
    db.refresh(job_import)

    return job_import, jobs_data, errors, scrape_meta


def enqueue_job_import(
    import_id: str, url: str, source: str, user_id: str
) -> Dict[str, Any]:
    """Dispatch a job import to the Celery scraping queue.

    Returns ``{"queued": True}`` on successful dispatch. If the broker is
    unreachable, runs the import synchronously inline and returns
    ``{"queued": False, "status": ...}`` — the documented synchronous fallback
    (broker failure makes the request block and completes inline).
    """
    try:
        from app.worker.tasks.scraping import scrape_and_import_job

        scrape_and_import_job.delay(
            import_id=str(import_id),
            url=url,
            source=source,
            user_id=str(user_id),
        )
        return {"queued": True}
    except Exception as exc:
        logger.warning(
            "celery_broker_unavailable_fallback_to_sync", extra={"error": str(exc)}
        )
        result = _scrape_and_import_job_sync(str(import_id), url, source, str(user_id))
        return {"queued": False, "status": result.get("status", "failed")}


def _scrape_and_import_job_sync(
    import_id: str, url: str, source: str, user_id: str
) -> Dict[str, Any]:
    """Run the import pipeline synchronously for a pre-created ``JobImport``.

    Delegates to the single authoritative pipeline (``process_import``) rather
    than re-fetching/parsing, then stamps ``processed_at`` on the terminal state.
    """
    db = SessionLocal()
    try:
        job_import = (
            db.query(JobImport).filter(JobImport.id == uuid.UUID(import_id)).first()
        )
        if not job_import:
            return {"status": "failed", "error": "JobImport not found"}

        job_import, jobs_data, errors, _ = process_import(
            db, uuid.UUID(user_id), source, url, existing_job_import=job_import
        )

        if not jobs_data:
            job_import.status = "failed"
            job_import.error = f"No jobs imported. Details: {errors}"
        elif errors:
            logger.warning(
                "partial_import_success",
                extra={"errors": errors, "import_id": import_id},
            )

        job_import.processed_at = datetime.now(timezone.utc)
        db.commit()

        return {"status": job_import.status}
    except Exception as exc:
        db.rollback()
        db2 = SessionLocal()
        try:
            ji = (
                db2.query(JobImport)
                .filter(JobImport.id == uuid.UUID(import_id))
                .first()
            )
            if ji:
                ji.status = "failed"
                ji.error = str(exc)[:500]
                ji.processed_at = datetime.now(timezone.utc)
                db2.commit()
        except Exception:
            db2.rollback()
        finally:
            db2.close()
        return {"status": "failed", "error": str(exc)[:500]}
    finally:
        db.close()
