"""
Profile versioning service (Sprint 2).

Handles:
- Creating immutable snapshots of profile state with schema versioning.
- No-op save detection to prevent redundant versions.
- Safe rollback by creating a new version from a previous snapshot.
- Retrieving version history and full snapshot details.
"""

from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.profile_version import ProfileVersion
from app.models.profile import (
    Profile,
    Experience,
    Education,
    Skill,
    Project,
    Certification,
)


MAX_VERSIONS = 50  # Retention policy — keep last 50 versions


def _parse_date(value: Any) -> date | None:
    """Parse a date string or date object into a Python date."""
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except (ValueError, TypeError):
            return None
    return None


def _profile_to_dict(profile: Profile) -> dict[str, Any]:
    """Serialize a Profile and all nested objects to a plain dict for storage."""
    return {
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "headline": profile.headline,
        "summary": profile.summary,
        "email": profile.email,
        "phone": profile.phone,
        "location": profile.location,
        "website": profile.website,
        "linkedin": profile.linkedin,
        "github": profile.github,
        "experiences": [
            {
                "title": e.title,
                "company": e.company,
                "location": e.location,
                "start_date": e.start_date.isoformat() if e.start_date else None,
                "end_date": e.end_date.isoformat() if e.end_date else None,
                "is_current": e.is_current,
                "description": e.description,
            }
            for e in (profile.experiences or [])
        ],
        "educations": [
            {
                "institution": ed.institution,
                "degree": ed.degree,
                "field_of_study": ed.field_of_study,
                "start_date": ed.start_date.isoformat() if ed.start_date else None,
                "end_date": ed.end_date.isoformat() if ed.end_date else None,
                "description": ed.description,
            }
            for ed in (profile.educations or [])
        ],
        "skills": [
            {
                "name": s.name,
                "category": s.category,
                "proficiency": s.proficiency,
            }
            for s in (profile.skills or [])
        ],
        "projects": [
            {
                "name": p.name,
                "description": p.description,
                "url": p.url,
                "start_date": p.start_date.isoformat() if p.start_date else None,
                "end_date": p.end_date.isoformat() if p.end_date else None,
            }
            for p in (profile.projects or [])
        ],
        "certifications": [
            {
                "name": c.name,
                "issuer": c.issuer,
                "issue_date": c.issue_date.isoformat() if c.issue_date else None,
                "expiration_date": c.expiration_date.isoformat()
                if c.expiration_date
                else None,
                "credential_id": c.credential_id,
                "credential_url": c.credential_url,
            }
            for c in (profile.certifications or [])
        ],
    }


def _extract_profile_data(snapshot_data: dict[str, Any]) -> dict[str, Any]:
    """Extract profile dict handling both schema_version wrappers and legacy bare dicts."""
    if not snapshot_data:
        return {}
    if "profile" in snapshot_data and isinstance(snapshot_data["profile"], dict):
        return snapshot_data["profile"]
    return snapshot_data


def create_profile_version(
    user_id: UUID,
    profile: Profile,
    db: Session,
    source: str = "update",
    reverted_from_version_id: Optional[UUID] = None,
    allow_noop: bool = False,
) -> ProfileVersion:
    """
    Create an immutable snapshot of the current profile state.
    - Uses schema-versioned envelope `{"schema_version": 1, "profile": {...}}`.
    - Detects no-ops: if incoming state matches latest version and source is 'update',
      reuses the latest version unless allow_noop=True.
    """
    latest = (
        db.query(ProfileVersion)
        .filter(ProfileVersion.user_id == user_id)
        .order_by(ProfileVersion.version.desc())
        .first()
    )

    current_profile_dict = _profile_to_dict(profile)

    # No-op check
    if latest and source == "update" and not allow_noop:
        latest_profile_dict = _extract_profile_data(latest.data or {})
        if latest_profile_dict == current_profile_dict:
            return latest

    next_version = (latest.version + 1) if latest else 1

    snapshot_envelope = {
        "schema_version": 1,
        "profile": current_profile_dict,
    }

    snapshot = ProfileVersion(
        user_id=user_id,
        version=next_version,
        data=snapshot_envelope,
        source=source,
        reverted_from_version_id=reverted_from_version_id,
    )
    db.add(snapshot)
    db.flush()

    # Enforce retention policy
    if next_version > MAX_VERSIONS:
        cutoff_version = next_version - MAX_VERSIONS
        (
            db.query(ProfileVersion)
            .filter(
                ProfileVersion.user_id == user_id,
                ProfileVersion.version <= cutoff_version,
            )
            .delete()
        )
        db.flush()

    return snapshot


def get_profile_history(user_id: UUID, db: Session, limit: int = 50) -> list[dict]:
    """
    Return all profile versions for a user, newest first.
    Each entry contains version number, timestamp, source, and a summary.
    """
    versions = (
        db.query(ProfileVersion)
        .filter(ProfileVersion.user_id == user_id)
        .order_by(ProfileVersion.version.desc())
        .limit(limit)
        .all()
    )

    result = []
    for v in versions:
        raw_data = v.data or {}
        profile_data = _extract_profile_data(raw_data)
        result.append(
            {
                "id": str(v.id),
                "version": v.version,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "source": v.source or "update",
                "summary": _build_version_summary(profile_data),
            }
        )

    return result


def get_profile_version_detail(
    user_id: UUID, version_id: UUID, db: Session
) -> dict[str, Any]:
    """
    Return full details of a specific profile version snapshot.
    """
    v = (
        db.query(ProfileVersion)
        .filter(
            ProfileVersion.id == version_id,
            ProfileVersion.user_id == user_id,
        )
        .first()
    )
    if not v:
        raise ValueError("Profile version not found")

    raw_data = v.data or {}
    profile_data = _extract_profile_data(raw_data)
    schema_version = (
        raw_data.get("schema_version", 1) if isinstance(raw_data, dict) else 1
    )

    return {
        "id": str(v.id),
        "user_id": str(v.user_id),
        "version": v.version,
        "created_at": v.created_at.isoformat() if v.created_at else None,
        "source": v.source or "update",
        "reverted_from_version_id": str(v.reverted_from_version_id)
        if v.reverted_from_version_id
        else None,
        "schema_version": schema_version,
        "profile": profile_data,
        "summary": _build_version_summary(profile_data),
    }


def _build_version_summary(data: dict) -> str:
    """Build a human-readable summary of what's in this version."""
    parts = []
    name = " ".join(filter(None, [data.get("first_name"), data.get("last_name")]))
    if name:
        parts.append(name)

    counts = []
    for section, label in [
        ("experiences", "experience"),
        ("educations", "education"),
        ("skills", "skill"),
        ("projects", "project"),
        ("certifications", "certification"),
    ]:
        items = data.get(section) or []
        if items:
            counts.append(f"{len(items)} {label}{'s' if len(items) != 1 else ''}")

    if counts:
        parts.append(", ".join(counts))

    return " — ".join(parts) if parts else "Empty profile"


def revert_to_version(user_id: UUID, version_id: UUID, db: Session) -> Profile:
    """
    Revert the user's profile to a specific version snapshot.
    - Restores fields from snapshot.
    - Creates a new immutable ProfileVersion with source="revert" and reverted_from_version_id.
    - Increments profile revision for concurrency tracking.
    """
    target = (
        db.query(ProfileVersion)
        .filter(
            ProfileVersion.id == version_id,
            ProfileVersion.user_id == user_id,
        )
        .first()
    )
    if not target:
        raise ValueError("Version not found")

    raw_data = target.data
    if not raw_data:
        raise ValueError("Version has no data")

    snapshot_data = _extract_profile_data(raw_data)

    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise ValueError("Profile not found")

    # Clear existing nested objects
    for field_name in [
        "experiences",
        "educations",
        "skills",
        "projects",
        "certifications",
    ]:
        getattr(profile, field_name).clear()

    # Restore top-level fields
    for field in [
        "first_name",
        "last_name",
        "headline",
        "summary",
        "email",
        "phone",
        "location",
        "website",
        "linkedin",
        "github",
    ]:
        setattr(profile, field, snapshot_data.get(field))

    # Restore nested objects
    for exp_data in snapshot_data.get("experiences", []):
        exp_dict = dict(exp_data)
        exp_dict["start_date"] = _parse_date(exp_dict.get("start_date"))
        exp_dict["end_date"] = _parse_date(exp_dict.get("end_date"))
        db.add(Experience(profile_id=profile.id, **exp_dict))

    for edu_data in snapshot_data.get("educations", []):
        edu_dict = dict(edu_data)
        edu_dict["start_date"] = _parse_date(edu_dict.get("start_date"))
        edu_dict["end_date"] = _parse_date(edu_dict.get("end_date"))
        db.add(Education(profile_id=profile.id, **edu_dict))

    for skill_data in snapshot_data.get("skills", []):
        db.add(Skill(profile_id=profile.id, **dict(skill_data)))

    for proj_data in snapshot_data.get("projects", []):
        proj_dict = dict(proj_data)
        proj_dict["start_date"] = _parse_date(proj_dict.get("start_date"))
        proj_dict["end_date"] = _parse_date(proj_dict.get("end_date"))
        db.add(Project(profile_id=profile.id, **proj_dict))

    for cert_data in snapshot_data.get("certifications", []):
        cert_dict = dict(cert_data)
        cert_dict["issue_date"] = _parse_date(cert_dict.get("issue_date"))
        cert_dict["expiration_date"] = _parse_date(cert_dict.get("expiration_date"))
        db.add(Certification(profile_id=profile.id, **cert_dict))

    # Concurrency revision increment
    profile.revision = (profile.revision or 1) + 1
    db.flush()

    # Record the revert as a new version
    create_profile_version(
        user_id=user_id,
        profile=profile,
        db=db,
        source="revert",
        reverted_from_version_id=target.id,
        allow_noop=True,
    )

    return profile
