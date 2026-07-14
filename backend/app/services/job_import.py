import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.job import Job, JobImport


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


# ─── Description Parsing ──────────────────────────────────────────────────

SENIORITY_KEYWORDS = [
    "senior", "staff", "principal", "lead", "junior", "mid", "associate",
    "intern", "graduate", "entry", "experienced",
]

SKILL_KEYWORDS = [
    "python", "javascript", "typescript", "go", "rust", "java", "c++", "c#",
    "react", "angular", "vue", "node", "nodejs", "django", "flask", "fastapi",
    "sql", "postgresql", "mysql", "mongodb", "redis", "aws", "gcp", "azure",
    "docker", "kubernetes", "terraform", "ci/cd", "git", "linux",
    "machine learning", "ai", "data science", "nlp", "computer vision",
    "rest api", "graphql", "grpc", "microservices", "distributed systems",
]


def extract_tags_from_text(text: str) -> List[str]:
    text_lower = text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        if skill in text_lower:
            found.append(skill)
    return found


def extract_field_from_text(text: str, field: str, keywords: List[str]) -> Optional[str]:
    lines = text.split("\n")
    for line in lines:
        line_lower = line.lower().strip()
        for kw in keywords:
            if kw in line_lower:
                colon_idx = line.find(":")
                if colon_idx == -1:
                    colon_idx = line.find("-")
                if colon_idx != -1 and colon_idx < len(line) - 1:
                    value = line[colon_idx + 1:].strip()
                    if value:
                        return value
    return None


TITLE_KEYWORDS = [
    "engineer", "developer", "scientist", "architect", "manager",
    "designer", "analyst", "intern", "specialist", "consultant",
]


def parse_job_from_description(description: str) -> Dict[str, Any]:
    lines = [line.strip() for line in description.split("\n") if line.strip()]

    title = "Unknown Position"
    if lines:
        first_line = lines[0]
        if any(kw in first_line.lower() for kw in TITLE_KEYWORDS):
            title = first_line

    company = extract_field_from_text(description, "company", [
        "company", "organization", "employer", "at ",
    ])

    location = extract_field_from_text(description, "location", [
        "location", "office", "site", "where",
    ])

    salary_text = extract_field_from_text(description, "salary", [
        "salary", "compensation", "pay", "range",
    ])
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
    title = normalize_for_dedup(job_data.get("title", ""))
    company = normalize_for_dedup(job_data.get("company", ""))
    location = normalize_for_dedup(job_data.get("location", "") or "")

    existing = db.query(Job).all()
    for job in existing:
        t_match = title and normalize_for_dedup(job.title) == title
        c_match = company and normalize_for_dedup(job.company) == company
        l_match = (not location or not job.location or
                   normalize_for_dedup(job.location) == location)
        if t_match and c_match and l_match:
            return True

    return False


# ─── Main Import Pipeline ─────────────────────────────────────────────────

def process_import(
    db: Session, user_id: uuid.UUID, source_type: str, data: str,
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
        if source_type == "url":
            parsed = parse_job_from_url(data)
        elif source_type == "description":
            if len(data.strip()) < 100:
                raise ValueError("Description must be at least 100 characters")
            parsed = parse_job_from_description(data)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

        normalized = normalize_job(parsed)

        is_dup = check_duplicate(db, normalized)

        if is_dup:
            job_import.fail_count += 1
            errors.append(f"Duplicate job: {normalized['title']} at {normalized['company']}")
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
