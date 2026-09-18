import hashlib
import logging
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core import metrics
from app.models.extension_token import ExtensionToken
from app.models.job import Job, JobImport, JobImportItem
from app.models.profile import Profile
from app.models.user import User
from app.schemas.agent import (
    ExtensionJobCaptureIn,
    ExtensionJobCaptureOut,
    ExtensionProfileOut,
)
from app.services.job_import import check_duplicate
from app.services.scraping.extraction import (
    detect_platform,
    extract_job_id_from_url,
    normalize_url,
)

logger = logging.getLogger(__name__)


def _sanitize_description(raw: str) -> str:
    """Sanitize description text, removing script/iframe tags and excess whitespace."""
    if not raw:
        return ""
    # Strip dangerous HTML script / iframe tags
    clean = re.sub(
        r"<(script|iframe|style)[^>]*>.*?</\1>",
        "",
        raw,
        flags=re.DOTALL | re.IGNORECASE,
    )
    # Strip HTML tags while preserving text formatting
    clean = re.sub(r"<[^>]+>", " ", clean)
    clean = re.sub(r"[ \t]+", " ", clean)
    clean = re.sub(r"\n\s*\n\s*\n+", "\n\n", clean)
    return clean.strip()


def hash_token(raw_token: str) -> str:
    """Compute deterministic SHA-256 hash of a raw extension token."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def create_extension_token(
    db: Session,
    user_id: uuid.UUID,
    name: str = "Browser Extension",
    expires_days: int = 30,
) -> Tuple[str, ExtensionToken]:
    """Generate a high-entropy extension token, store its hash, and return (raw_token, record)."""
    raw_token = f"srf_ext_{secrets.token_urlsafe(32)}"
    token_h = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

    token_record = ExtensionToken(
        user_id=user_id,
        token_hash=token_h,
        name=name[:100],
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(token_record)
    db.commit()
    db.refresh(token_record)
    return raw_token, token_record


def authenticate_extension_token(db: Session, raw_token: str) -> Optional[User]:
    """Verify an extension token and return the owning User if valid and active."""
    if not raw_token:
        return None

    token_h = hash_token(raw_token)
    token_record = (
        db.query(ExtensionToken).filter(ExtensionToken.token_hash == token_h).first()
    )

    if not token_record:
        return None

    if token_record.is_revoked:
        return None

    now = datetime.now(timezone.utc)
    expires_at = token_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        return None

    # Update last_used_at timestamp
    token_record.last_used_at = now
    db.commit()

    user = db.query(User).filter(User.id == token_record.user_id).first()
    if user and user.is_active:
        return user

    return None


def revoke_extension_token(db: Session, raw_token: str) -> bool:
    """Revoke an active extension token."""
    if not raw_token:
        return False

    token_h = hash_token(raw_token)
    token_record = (
        db.query(ExtensionToken).filter(ExtensionToken.token_hash == token_h).first()
    )
    if token_record:
        token_record.is_revoked = True
        db.commit()
        return True
    return False


def get_candidate_profile_for_autofill(
    db: Session, user_id: uuid.UUID
) -> ExtensionProfileOut:
    """Export safe candidate profile fields specifically mapped for application autofill."""
    user = db.query(User).filter(User.id == user_id).first()
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    first_name = profile.first_name if profile and profile.first_name else None
    last_name = profile.last_name if profile and profile.last_name else None
    full_name = user.full_name if user and user.full_name else None

    if not full_name and (first_name or last_name):
        full_name = f"{first_name or ''} {last_name or ''}".strip() or None
    elif full_name and not (first_name and last_name):
        parts = full_name.split(None, 1)
        if not first_name:
            first_name = parts[0]
        if not last_name and len(parts) > 1:
            last_name = parts[1]

    email = (profile.email if profile and profile.email else None) or (
        user.email if user else None
    )
    phone = profile.phone if profile and profile.phone else None
    location = profile.location if profile and profile.location else None
    headline = profile.headline if profile and profile.headline else None
    summary = profile.summary if profile and profile.summary else None
    website = profile.website if profile and profile.website else None
    linkedin = profile.linkedin if profile and profile.linkedin else None
    github = profile.github if profile and profile.github else None

    skills = []
    if profile and profile.skills:
        skills = [s.name for s in profile.skills if s.name]

    return ExtensionProfileOut(
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        headline=headline,
        summary=summary,
        email=email,
        phone=phone,
        location=location,
        website=website,
        linkedin=linkedin,
        github=github,
        skills=skills,
    )


def import_extension_capture(
    db: Session, user_id: uuid.UUID, capture: ExtensionJobCaptureIn
) -> ExtensionJobCaptureOut:
    """Ingest a job capture from the extension into the authoritative JobImport/Job model.

    Enforces idempotency, URL normalization, deduplication, and atomic lifecycle states.
    """
    clean_url = normalize_url(capture.page_url)
    platform = capture.platform or detect_platform(clean_url) or "generic"
    clean_job_id = extract_job_id_from_url(clean_url)

    if clean_job_id:
        external_id = f"{platform}:{clean_job_id}"
    else:
        url_hash = hashlib.sha256(clean_url.encode("utf-8")).hexdigest()[:16]
        external_id = f"ext:{platform}:{url_hash}"

    cleaned_description = _sanitize_description(capture.description)

    # 1. Initialize JobImport in processing status
    job_import = JobImport(
        user_id=user_id,
        source="extension",
        status="processing",
        source_data=clean_url[:2000],
        parsed_data={
            "capture_id": capture.capture_id,
            "platform": platform,
            "external_id": external_id,
            "confidence": capture.confidence,
            "extracted_via": capture.extracted_via,
        },
    )
    db.add(job_import)
    db.commit()
    db.refresh(job_import)

    metrics.JOB_IMPORTS_TOTAL.labels("extension").inc()

    try:
        # 2. Check for duplicate against Job table
        candidate_dict = {
            "external_id": external_id,
            "url": clean_url,
            "title": capture.title,
            "company": capture.company,
            "location": capture.location,
        }

        existing_job = check_duplicate(db, candidate_dict)

        if existing_job:
            # Duplicate detected
            job_import.fail_count = 1
            job_import.ok_count = 0
            job_import.total_found = 1
            job_import.status = "completed"
            job_import.errors = [f"Duplicate job: {capture.title} at {capture.company}"]

            db.add(
                JobImportItem(
                    import_id=job_import.id,
                    job_id=existing_job.id,
                    status="duplicate",
                    title_guess=capture.title,
                )
            )
            db.commit()
            metrics.JOB_IMPORTS_DUPLICATE.inc()

            return ExtensionJobCaptureOut(
                success=True,
                status="duplicate",
                job_id=str(existing_job.id),
                import_id=str(job_import.id),
                capture_id=capture.capture_id,
                title=capture.title,
                company=capture.company,
                message="Job already exists in your workspace",
            )

        # 3. New Job creation
        job = Job(
            external_id=external_id,
            title=capture.title,
            company=capture.company,
            location=capture.location,
            description=cleaned_description,
            salary_min=capture.salary_min,
            salary_max=capture.salary_max,
            currency=capture.currency or "USD",
            tags=capture.tags or ([platform] if platform else []),
            url=clean_url,
            source="extension",
            import_id=job_import.id,
        )
        db.add(job)
        db.flush()

        # 4. Add JobImportItem and mark JobImport completed
        db.add(
            JobImportItem(
                import_id=job_import.id,
                job_id=job.id,
                status="imported",
                title_guess=capture.title,
            )
        )

        job_import.ok_count = 1
        job_import.fail_count = 0
        job_import.total_found = 1
        job_import.status = "completed"
        job_import.errors = []

        db.commit()
        db.refresh(job)

        return ExtensionJobCaptureOut(
            success=True,
            status="imported",
            job_id=str(job.id),
            import_id=str(job_import.id),
            capture_id=capture.capture_id,
            title=job.title,
            company=job.company,
            message="Job successfully captured into SiraFit",
        )

    except Exception as e:
        logger.exception("Error processing extension capture")
        db.rollback()
        job_import.status = "failed"
        job_import.fail_count = 1
        job_import.total_found = 1
        job_import.errors = [str(e)]
        db.add(
            JobImportItem(
                import_id=job_import.id,
                job_id=None,
                status="failed",
                error_message=str(e),
                title_guess=capture.title,
            )
        )
        db.commit()
        metrics.JOB_IMPORTS_FAILED.inc()

        return ExtensionJobCaptureOut(
            success=False,
            status="failed",
            job_id=None,
            import_id=str(job_import.id),
            capture_id=capture.capture_id,
            title=capture.title,
            company=capture.company,
            message=f"Capture failed: {str(e)}",
        )
