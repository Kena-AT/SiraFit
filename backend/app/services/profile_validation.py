"""
Business-level profile validation (Sprint 2).

Runs before persistence to catch invalid data:
- Date range ordering (start_date <= end_date)
- Current role invariants (no end_date if is_current is True)
- Required nested fields (title, company, institution, name, issuer)
- Syntax validation for URLs
- Structured field-level errors (code, path, message)
"""

from datetime import date
import re
from typing import Any


class ProfileValidationError(str):
    """
    Validation error item that inherits from str for full backward compatibility
    with existing tests while exposing structured attributes (code, path, message).
    """

    code: str
    path: str
    message: str

    def __new__(cls, message: str, code: str = "VALIDATION_ERROR", path: str = ""):
        obj = super().__new__(cls, message)
        obj.message = message
        obj.code = code
        obj.path = path
        return obj

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


def _is_valid_url(url: str) -> bool:
    if not url:
        return True
    pattern = re.compile(
        r"^(https?://)?"  # optional scheme
        r"([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}"  # domain
        r"(:\d+)?"  # optional port
        r"(/.*)?$",  # optional path
        re.IGNORECASE,
    )
    return bool(pattern.match(url.strip()))


def validate_experience_dates(experiences: list[dict]) -> list[ProfileValidationError]:
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
                errors.append(
                    ProfileValidationError(
                        f"{label}: end date ({end}) precedes start date ({start})",
                        code="INVALID_DATE_RANGE",
                        path=f"experiences[{i}].end_date",
                    )
                )

        if is_current and end:
            errors.append(
                ProfileValidationError(
                    f"Experience '{exp.get('title', f'#{i + 1}')}' is marked current but has an end date",
                    code="INVALID_CURRENT_STATE",
                    path=f"experiences[{i}].end_date",
                )
            )

    return errors


def validate_education_dates(educations: list[dict]) -> list[ProfileValidationError]:
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
                errors.append(
                    ProfileValidationError(
                        f"{label}: end date ({end}) precedes start date ({start})",
                        code="INVALID_DATE_RANGE",
                        path=f"educations[{i}].end_date",
                    )
                )
    return errors


def validate_project_dates(projects: list[dict]) -> list[ProfileValidationError]:
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
                errors.append(
                    ProfileValidationError(
                        f"{label}: end date ({end}) precedes start date ({start})",
                        code="INVALID_DATE_RANGE",
                        path=f"projects[{i}].end_date",
                    )
                )
    return errors


def validate_required_fields(profile_data: dict) -> list[ProfileValidationError]:
    """Ensure at least first_name or headline is set when identity fields are present."""
    errors = []
    name_keys = {"first_name", "last_name", "headline"}
    if not any(k in profile_data for k in name_keys):
        return errors

    first_name = (
        profile_data.get("first_name", "").strip()
        if profile_data.get("first_name")
        else ""
    )
    last_name = (
        profile_data.get("last_name", "").strip()
        if profile_data.get("last_name")
        else ""
    )
    headline = (
        profile_data.get("headline", "").strip() if profile_data.get("headline") else ""
    )

    if not first_name and not last_name and not headline:
        errors.append(
            ProfileValidationError(
                "At least one of: first name, last name, or professional headline is required",
                code="REQUIRED_FIELD",
                path="profile",
            )
        )

    return errors


def validate_experiences(experiences: list[dict]) -> list[ProfileValidationError]:
    """Validate experience entries have required fields."""
    errors = []
    for i, exp in enumerate(experiences):
        if not exp.get("title", "").strip():
            errors.append(
                ProfileValidationError(
                    f"Experience #{i + 1}: title is required",
                    code="REQUIRED_FIELD",
                    path=f"experiences[{i}].title",
                )
            )
        if not exp.get("company", "").strip():
            errors.append(
                ProfileValidationError(
                    f"Experience #{i + 1}: company is required",
                    code="REQUIRED_FIELD",
                    path=f"experiences[{i}].company",
                )
            )
    return errors


def validate_educations(educations: list[dict]) -> list[ProfileValidationError]:
    """Validate education entries have required fields."""
    errors = []
    for i, edu in enumerate(educations):
        if not edu.get("institution", "").strip():
            errors.append(
                ProfileValidationError(
                    f"Education #{i + 1}: institution is required",
                    code="REQUIRED_FIELD",
                    path=f"educations[{i}].institution",
                )
            )
    return errors


def validate_projects(projects: list[dict]) -> list[ProfileValidationError]:
    """Validate project entries have required fields and valid URLs."""
    errors = []
    for i, proj in enumerate(projects):
        if not proj.get("name", "").strip():
            errors.append(
                ProfileValidationError(
                    f"Project #{i + 1}: name is required",
                    code="REQUIRED_FIELD",
                    path=f"projects[{i}].name",
                )
            )
        url = proj.get("url")
        if url and not _is_valid_url(url):
            errors.append(
                ProfileValidationError(
                    f"Project #{i + 1}: invalid URL format",
                    code="INVALID_URL",
                    path=f"projects[{i}].url",
                )
            )
    return errors


def validate_skills(skills: list[dict]) -> list[ProfileValidationError]:
    """Validate skill entries have required fields."""
    errors = []
    for i, skill in enumerate(skills):
        if not skill.get("name", "").strip():
            errors.append(
                ProfileValidationError(
                    f"Skill #{i + 1}: name is required",
                    code="REQUIRED_FIELD",
                    path=f"skills[{i}].name",
                )
            )
    return errors


def validate_certifications(certifications: list[dict]) -> list[ProfileValidationError]:
    """Validate certification entries have required fields and valid dates/URLs."""
    errors = []
    for i, cert in enumerate(certifications):
        if not cert.get("name", "").strip():
            errors.append(
                ProfileValidationError(
                    f"Certification #{i + 1}: name is required",
                    code="REQUIRED_FIELD",
                    path=f"certifications[{i}].name",
                )
            )
        if not cert.get("issuer", "").strip():
            errors.append(
                ProfileValidationError(
                    f"Certification #{i + 1}: issuer is required",
                    code="REQUIRED_FIELD",
                    path=f"certifications[{i}].issuer",
                )
            )
        url = cert.get("credential_url")
        if url and not _is_valid_url(url):
            errors.append(
                ProfileValidationError(
                    f"Certification #{i + 1}: invalid credential URL format",
                    code="INVALID_URL",
                    path=f"certifications[{i}].credential_url",
                )
            )
        issue_date = cert.get("issue_date")
        exp_date = cert.get("expiration_date")
        if issue_date and exp_date:
            if isinstance(issue_date, str):
                issue_date = date.fromisoformat(issue_date)
            if isinstance(exp_date, str):
                exp_date = date.fromisoformat(exp_date)
            if exp_date < issue_date:
                errors.append(
                    ProfileValidationError(
                        f"Certification #{i + 1}: expiration date precedes issue date",
                        code="INVALID_DATE_RANGE",
                        path=f"certifications[{i}].expiration_date",
                    )
                )
    return errors


def validate_profile(profile_data: dict[str, Any]) -> list[ProfileValidationError]:
    """
    Run all business validations on profile data.
    Returns a list of ProfileValidationError objects. Empty list = valid.
    """
    errors: list[ProfileValidationError] = []

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
