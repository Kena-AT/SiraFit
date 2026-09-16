"""
Business-level profile validation.

Runs before persistence to catch invalid data that Pydantic schema validation
doesn't cover (date ordering, required nested fields, skill taxonomy checks).
"""
from datetime import date
from typing import Any


def validate_experience_dates(experiences: list[dict]) -> list[str]:
    """Ensure no end date precedes its start date, and current roles have no end date."""
    errors = []
    for i, exp in enumerate(experiences):
        start = exp.get("start_date")
        end = exp.get("end_date")
        is_current = exp.get("is_current", False)

        if start and end and not is_current:
            if isinstance(start, str):
                start = date.fromisoformat(start)
            if isinstance(end, str):
                end = date.fromisoformat(end)
            if start and end and end < start:
                label = exp.get("title") or f"Experience #{i + 1}"
                errors.append(f"{label}: end date ({end}) precedes start date ({start})")

        if is_current and end:
            errors.append(f"Experience '{exp.get('title', f'#{i + 1}')}' is marked current but has an end date")

    return errors


def validate_education_dates(educations: list[dict]) -> list[str]:
    """Ensure no end date precedes its start date."""
    errors = []
    for i, edu in enumerate(educations):
        start = edu.get("start_date")
        end = edu.get("end_date")
        if start and end:
            if isinstance(start, str):
                start = date.fromisoformat(start)
            if isinstance(end, str):
                end = date.fromisoformat(end)
            if start and end and end < start:
                label = edu.get("institution") or f"Education #{i + 1}"
                errors.append(f"{label}: end date ({end}) precedes start date ({start})")
    return errors


def validate_project_dates(projects: list[dict]) -> list[str]:
    """Ensure no end date precedes its start date."""
    errors = []
    for i, proj in enumerate(projects):
        start = proj.get("start_date")
        end = proj.get("end_date")
        if start and end:
            if isinstance(start, str):
                start = date.fromisoformat(start)
            if isinstance(end, str):
                end = date.fromisoformat(end)
            if start and end and end < start:
                label = proj.get("name") or f"Project #{i + 1}"
                errors.append(f"{label}: end date ({end}) precedes start date ({start})")
    return errors


def validate_required_fields(profile_data: dict) -> list[str]:
    """Ensure at least first_name or headline is set."""
    errors = []
    first_name = profile_data.get("first_name", "").strip() if profile_data.get("first_name") else ""
    last_name = profile_data.get("last_name", "").strip() if profile_data.get("last_name") else ""
    headline = profile_data.get("headline", "").strip() if profile_data.get("headline") else ""

    if not first_name and not last_name and not headline:
        errors.append("At least one of: first name, last name, or professional headline is required")

    return errors


def validate_experiences(experiences: list[dict]) -> list[str]:
    """Validate experience entries have required fields."""
    errors = []
    for i, exp in enumerate(experiences):
        if not exp.get("title", "").strip():
            errors.append(f"Experience #{i + 1}: title is required")
        if not exp.get("company", "").strip():
            errors.append(f"Experience #{i + 1}: company is required")
    return errors


def validate_educations(educations: list[dict]) -> list[str]:
    """Validate education entries have required fields."""
    errors = []
    for i, edu in enumerate(educations):
        if not edu.get("institution", "").strip():
            errors.append(f"Education #{i + 1}: institution is required")
    return errors


def validate_projects(projects: list[dict]) -> list[str]:
    """Validate project entries have required fields."""
    errors = []
    for i, proj in enumerate(projects):
        if not proj.get("name", "").strip():
            errors.append(f"Project #{i + 1}: name is required")
    return errors


def validate_skills(skills: list[dict]) -> list[str]:
    """Validate skill entries have required fields."""
    errors = []
    for i, skill in enumerate(skills):
        if not skill.get("name", "").strip():
            errors.append(f"Skill #{i + 1}: name is required")
    return errors


def validate_certifications(certifications: list[dict]) -> list[str]:
    """Validate certification entries have required fields."""
    errors = []
    for i, cert in enumerate(certifications):
        if not cert.get("name", "").strip():
            errors.append(f"Certification #{i + 1}: name is required")
        if not cert.get("issuer", "").strip():
            errors.append(f"Certification #{i + 1}: issuer is required")
    return errors


def validate_profile(profile_data: dict[str, Any]) -> list[str]:
    """
    Run all business validations on profile data.
    Returns a list of human-readable error strings. Empty list = valid.
    """
    errors: list[str] = []

    errors.extend(validate_required_fields(profile_data))
    errors.extend(validate_experiences(profile_data.get("experiences") or []))
    errors.extend(validate_educations(profile_data.get("educations") or []))
    errors.extend(validate_projects(profile_data.get("projects") or []))
    errors.extend(validate_skills(profile_data.get("skills") or []))
    errors.extend(validate_certifications(profile_data.get("certifications") or []))
    errors.extend(validate_experience_dates(profile_data.get("experiences") or []))
    errors.extend(validate_education_dates(profile_data.get("educations") or []))
    errors.extend(validate_project_dates(profile_data.get("projects") or []))

    return errors
