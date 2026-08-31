import re
import uuid
import csv
import io
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import json

from sqlalchemy.orm import Session

from app.models.job import Job, JobImport

# ─── Scrapling (optional scraping engine) ───────────────────────────────────
# Scrapling provides stealthy + adaptive web fetching/parsing. It is an OPTIONAL
# dependency: if it isn't installed, the importer falls back to the heuristic URL
# parser below (title/company guessed from the URL, no page fetch).
try:
    from scrapling import Fetcher, Selector

    _SCRAPLING_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    _SCRAPLING_AVAILABLE = False


# ─── URL Platform Detection ───────────────────────────────────────────────


def detect_platform(url: str) -> Optional[str]:
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


# ─── URL Parsing ──────────────────────────────────────────────────────────


def parse_job_from_url(url: str) -> Dict[str, Any]:
    platform = detect_platform(url)
    job_id = extract_job_id_from_url(url)

    company_hints = {
        "linkedin": "LinkedIn",
        "indeed": "Indeed",
        "glassdoor": "Glassdoor",
        "ziprecruiter": "ZipRecruiter",
        "simplyhired": "SimplyHired",
        "lever": "Unknown Company (Lever)",
        "greenhouse": "Unknown Company (Greenhouse)",
        "ashby": "Unknown Company (Ashby)",
        "workday": "Unknown Company (Workday)",
    }

    title = "Unknown Position"
    company = company_hints.get(platform, "Unknown Source")

    path_segments = urlparse(url).path.strip("/").split("/")
    for seg in reversed(path_segments):
        seg = seg.replace("-", " ").replace("_", " ").title()
        if seg and seg not in ("Jobs", "Job", "View"):
            title = seg
            break

    return {
        "title": title,
        "company": company,
        "location": None,
        "description": None,
        "salary_min": None,
        "salary_max": None,
        "currency": None,
        "tags": [platform] if platform else [],
        "url": url,
        "source": platform or "url",
        "external_id": str(job_id or uuid.uuid4()),
    }


# ─── Scrapling fetch + parse ────────────────────────────────────────────────


def _clean_html_to_text(html_fragment: str) -> str:
    """Strip HTML tags and collapse whitespace into plain text."""
    text = re.sub(r"<[^>]+>", " ", html_fragment or "")
    return re.sub(r"\s+", " ", text).strip()


def fetch_job_html(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch a job page with Scrapling; return raw HTML or None on any failure.

    Uses the stealthy (curl_cffi) engine — no browser binaries required. To also
    use the adaptive browser fallback for JS-heavy boards, run ``scrapling install``
    and configure ``Fetcher.configure(adaptive=True, stealthy=True)`` instead.
    """
    if not _SCRAPLING_AVAILABLE:
        return None
    try:
        Fetcher.configure(stealthy=True)
        response = Fetcher.get(
            url, timeout=timeout, follow_redirects=True, retries=2
        )
        if response is None:
            return None
        body = getattr(response, "body", None)
        if not body:
            return None
        return body if isinstance(body, str) else body.decode("utf-8", "replace")
    except Exception:
        return None


def parse_job_html(html: str, url: str) -> Dict[str, Any]:
    """Extract structured job fields from fetched HTML using Scrapling.

    Strategy: JSON-LD JobPosting → meta/Open-Graph tags → DOM heuristics.
    Returns the same dict shape as ``parse_job_from_url`` so the two merge cleanly.
    """
    platform = detect_platform(url)
    job_id = extract_job_id_from_url(url)
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
        location = sel.css('meta[property="og:locale"]::attr(content)').get()

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
        salary_text = extract_field_from_text(
            description, "salary", ["salary", "compensation", "pay", "range"]
        )
        if salary_text:
            nums = re.findall(r"\d[\d,]*", salary_text.replace(",", ""))
            if len(nums) >= 2:
                salary_min = int(nums[0])
                salary_max = int(nums[1])
            elif len(nums) == 1:
                salary_max = int(nums[0])

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
    text_lower = text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        if skill in text_lower:
            found.append(skill)
    return found


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
                    if line and not line.lower().startswith("url") and not line.lower().startswith("link"):
                        if line.startswith("http://") or line.startswith("https://"):
                            jobs.append(parse_job_from_url(line))
                        else:
                            jobs.append(parse_job_from_description(line))
                return jobs

            for row in reader:
                row_lower = {k.lower().strip(): v for k, v in row.items() if k}
                url = row_lower.get("url") or row_lower.get("link") or row_lower.get("job_url")
                title = row_lower.get("title") or row_lower.get("job_title") or row_lower.get("position")
                company = row_lower.get("company") or row_lower.get("employer") or row_lower.get("organization")
                location = row_lower.get("location") or row_lower.get("place") or row_lower.get("office")
                description = row_lower.get("description") or row_lower.get("desc") or row_lower.get("details")

                if url and not title:
                    parsed_url_job = parse_job_from_url(url)
                    if company:
                        parsed_url_job["company"] = company
                    if location:
                        parsed_url_job["location"] = location
                    jobs.append(parsed_url_job)
                elif title or description:
                    jobs.append({
                        "title": title or "Unknown Position",
                        "company": company or "Unknown Company",
                        "location": location,
                        "description": description or (f"Position: {title} at {company}" if title and company else "Imported from CSV"),
                        "salary_min": None,
                        "salary_max": None,
                        "currency": "USD",
                        "tags": extract_tags_from_text(description or title or ""),
                        "url": url,
                        "source": "csv",
                        "external_id": str(uuid.uuid4()),
                    })
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
    except Exception as e:
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


def check_duplicate(db: Session, job_data: Dict[str, Any]) -> bool:
    """Check if a job already exists using indexed lookups instead of full table scan.

    Instead of loading ALL jobs (O(n)), use targeted queries by title+company.
    This is O(1) with proper database indexes.
    """
    title = job_data.get("title", "")
    company = job_data.get("company", "")
    location = job_data.get("location", "") or ""

    # Build filtered query — only check title and company, location is soft
    query = db.query(Job)

    if title:
        # Case-insensitive partial match on title
        query = query.filter(Job.title.ilike(f"%{title}%"))

    if company:
        # Case-insensitive partial match on company
        query = query.filter(Job.company.ilike(f"%{company}%"))

    # Location is optional — if provided, add filter; if not, skip (doesn't block match)
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    # Check if any matching job exists
    exists = query.limit(1).first() is not None

    return exists


# ─── Main Import Pipeline ─────────────────────────────────────────────────


def process_import(
    db: Session,
    user_id: uuid.UUID,
    source_type: str,
    data: str,
) -> Tuple[JobImport, List[Dict[str, Any]]]:
    job_import = JobImport(
        user_id=user_id,
        source=source_type,
        status="processing",
    )
    db.add(job_import)
    db.commit()
    db.refresh(job_import)

    errors = []
    jobs_data = []

    try:
        parsed_list = []
        if source_type == "url":
            parsed = parse_job_from_url(data)
            # ── Enrichment-first: try scrapping, fall back to heuristic ──────
            # We always attempt a real-page fetch when Scrapling is available.
            # On success, enriched fields (title, company, description, salary,
            # tags) override the heuristic parser values.  On any failure
            # (no network, parse error, resistant board) the heuristic data
            # is kept intact — the import never breaks because scrapping failed.
            html = fetch_job_html(data)
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
                # if enriched is None: keep heuristic data as-is
            # if html is None (scrapling unavailable / network error):
            #   — keep the heuristic parse from parse_job_from_url as-is
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

            is_dup = check_duplicate(db, normalized)

            if is_dup:
                job_import.fail_count += 1
                errors.append(
                    f"Duplicate job: {normalized['title']} at {normalized['company']}"
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
                )
                db.add(job)
                db.commit()
                db.refresh(job)
                job_import.ok_count += 1
                jobs_data.append(normalized)

        job_import.total_found = job_import.ok_count + job_import.fail_count
        job_import.status = "completed"

    except Exception as e:
        job_import.status = "failed"
        job_import.fail_count += 1
        errors.append(str(e))

    db.commit()
    db.refresh(job_import)

    return job_import, jobs_data, errors
