"""
Resume Versioning Service.

Handles resume version lineage, immutability, revert snapshots, and base versions.
All database sessions are injected; never creates rogue sessions.
"""

import json
import logging
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.job import Resume, ResumeVersion
from app.models.profile import Profile
from app.schemas.resume import ResumeDiffResponse
from app.services.resume_diff import compute_resume_diff

logger = logging.getLogger(__name__)


def create_base_version_from_profile(
    db: Session,
    resume: Resume,
    profile: Profile,
    template: str = "minimal",
) -> ResumeVersion:
    """
    Ensure exactly one base snapshot exists for the resume.
    If a base version already exists, returns it.
    Otherwise, builds snapshot content from the user's master Profile and creates a base version.
    """
    existing_base = (
        db.query(ResumeVersion)
        .filter(
            ResumeVersion.resume_id == resume.id, ResumeVersion.source_type == "base"
        )
        .first()
    )
    if existing_base:
        return existing_base

    # Build base content JSON from Profile
    experience_list = []
    for exp in profile.experiences or []:
        bullets = [b.strip() for b in (exp.description or "").split("\n") if b.strip()]
        period = f"{exp.start_date.strftime('%b %Y') if exp.start_date else ''} - {exp.end_date.strftime('%b %Y') if exp.end_date else ('Present' if exp.is_current else '')}".strip(
            " -"
        )
        experience_list.append(
            {
                "title": exp.title,
                "company": exp.company,
                "location": exp.location,
                "period": period or None,
                "bullets": bullets,
            }
        )

    education_list = []
    for edu in profile.educations or []:
        period = f"{edu.start_date.strftime('%Y') if edu.start_date else ''} - {edu.end_date.strftime('%Y') if edu.end_date else ''}".strip(
            " -"
        )
        education_list.append(
            {
                "institution": edu.institution,
                "degree": edu.degree,
                "field_of_study": edu.field_of_study,
                "period": period or None,
            }
        )

    projects_list = []
    for proj in profile.projects or []:
        projects_list.append(
            {
                "name": proj.name,
                "description": proj.description,
                "url": proj.url,
            }
        )

    skills_list = [s.name for s in (profile.skills or [])]

    base_data = {
        "name": f"{profile.first_name or ''} {profile.last_name or ''}".strip(),
        "email": profile.email or "",
        "phone": profile.phone or "",
        "location": profile.location or "",
        "linkedin": profile.linkedin or "",
        "github": profile.github or "",
        "website": profile.website or "",
        "summary": profile.summary or "",
        "experience": experience_list,
        "projects": projects_list,
        "skills": skills_list,
        "education": education_list,
    }

    # Find next version number
    latest = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume.id)
        .order_by(ResumeVersion.version_number.desc())
        .first()
    )
    next_version = (latest.version_number + 1) if latest else 1

    base_version = ResumeVersion(
        resume_id=resume.id,
        version_number=next_version,
        content=json.dumps(base_data),
        template=template,
        job_id=None,
        parent_version_id=None,
        source_type="base",
        tailoring_notes="Canonical base snapshot derived from master profile",
        score=None,
        status="completed",
    )
    db.add(base_version)
    db.commit()
    db.refresh(base_version)
    return base_version


def revert_to_version(
    db: Session,
    resume_id: uuid.UUID,
    target_version_id: uuid.UUID,
    current_user_id: uuid.UUID,
) -> ResumeVersion:
    """
    Reverts to an older version by creating a NEW immutable ResumeVersion snapshot.
    Historical versions are never mutated.
    - source_type = 'revert'
    - parent_version_id = target_version_id
    """
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user_id)
        .first()
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
        )

    target_version = (
        db.query(ResumeVersion)
        .filter(
            ResumeVersion.id == target_version_id, ResumeVersion.resume_id == resume_id
        )
        .first()
    )
    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Target version not found"
        )

    # Next version number
    latest = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume_id)
        .order_by(ResumeVersion.version_number.desc())
        .first()
    )
    next_version = (latest.version_number + 1) if latest else 1

    # Preserve job association and score if reverting a tailored version, or clear if reverting to base
    new_version = ResumeVersion(
        resume_id=resume_id,
        version_number=next_version,
        content=target_version.content,
        template=target_version.template,
        job_id=target_version.job_id,
        parent_version_id=target_version.id,
        source_type="revert",
        tailoring_notes=f"Reverted to version v{target_version.version_number}",
        score=target_version.score,
        status="completed",
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return new_version


def compare_resume_versions(
    db: Session,
    resume_id: uuid.UUID,
    version_a_id: uuid.UUID,
    version_b_id: uuid.UUID,
    current_user_id: uuid.UUID,
) -> ResumeDiffResponse:
    """
    Compare two versions belonging to the authenticated user's resume.
    """
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user_id)
        .first()
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
        )

    v_a = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.id == version_a_id, ResumeVersion.resume_id == resume_id)
        .first()
    )
    if not v_a:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version A not found on this resume",
        )

    v_b = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.id == version_b_id, ResumeVersion.resume_id == resume_id)
        .first()
    )
    if not v_b:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version B not found on this resume",
        )

    return compute_resume_diff(
        from_version_id=v_a.id,
        to_version_id=v_b.id,
        from_version_number=v_a.version_number,
        to_version_number=v_b.version_number,
        from_content_raw=v_a.content,
        to_content_raw=v_b.content,
    )
