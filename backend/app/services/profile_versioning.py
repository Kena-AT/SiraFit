"""
Profile versioning service.

Handles creating immutable snapshots of the profile before each update,
retrieving version history, and reverting to a previous version.
"""
from datetime import date, datetime
from typing import Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.profile_version import ProfileVersion
from app.models.profile import Profile, Experience, Education, Skill, Project, Certification


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
                "expiration_date": c.expiration_date.isoformat() if c.expiration_date else None,
                "credential_id": c.credential_id,
                "credential_url": c.credential_url,
            }
            for c in (profile.certifications or [])
        ],
    }


def create_profile_version(user_id: UUID, profile: Profile, db: Session) -> ProfileVersion:
    """
    Create an immutable snapshot of the current profile state.
    Returns the new ProfileVersion.
    """
    # Get next version number
    latest = (
        db.query(ProfileVersion)
        .filter(ProfileVersion.user_id == user_id)
        .order_by(ProfileVersion.version.desc())
        .first()
    )
    next_version = (latest.version + 1) if latest else 1

    snapshot = ProfileVersion(
        user_id=user_id,
        version=next_version,
        data=_profile_to_dict(profile),
    )
    db.add(snapshot)
    db.flush()

    # Enforce retention policy — keep last MAX_VERSIONS, delete older ones
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
    Each entry contains version number, timestamp, and a summary of changes.
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
        data = v.data or {}
        result.append({
            "id": str(v.id),
            "version": v.version,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "summary": _build_version_summary(data),
        })

    return result


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
    Creates a version of the current state first, then restores from the snapshot.
    """
    # Get the target version
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

    snapshot_data = target.data
    if not snapshot_data:
        raise ValueError("Version has no data")

    # Get current profile
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise ValueError("Profile not found")

    # Create a version of the current state before reverting
    create_profile_version(user_id, profile, db)

    # Clear existing nested objects
    for field_name in ["experiences", "educations", "skills", "projects", "certifications"]:
        getattr(profile, field_name).clear()

    # Restore top-level fields
    for field in [
        "first_name", "last_name", "headline", "summary",
        "email", "phone", "location", "website", "linkedin", "github",
    ]:
        setattr(profile, field, snapshot_data.get(field))

    # Restore nested objects
    for exp_data in snapshot_data.get("experiences", []):
        exp_data["start_date"] = _parse_date(exp_data.get("start_date"))
        exp_data["end_date"] = _parse_date(exp_data.get("end_date"))
        db.add(Experience(profile_id=profile.id, **exp_data))
    for edu_data in snapshot_data.get("educations", []):
        edu_data["start_date"] = _parse_date(edu_data.get("start_date"))
        edu_data["end_date"] = _parse_date(edu_data.get("end_date"))
        db.add(Education(profile_id=profile.id, **edu_data))
    for skill_data in snapshot_data.get("skills", []):
        db.add(Skill(profile_id=profile.id, **skill_data))
    for proj_data in snapshot_data.get("projects", []):
        proj_data["start_date"] = _parse_date(proj_data.get("start_date"))
        proj_data["end_date"] = _parse_date(proj_data.get("end_date"))
        db.add(Project(profile_id=profile.id, **proj_data))
    for cert_data in snapshot_data.get("certifications", []):
        cert_data["issue_date"] = _parse_date(cert_data.get("issue_date"))
        cert_data["expiration_date"] = _parse_date(cert_data.get("expiration_date"))
        db.add(Certification(profile_id=profile.id, **cert_data))

    db.flush()
    return profile
