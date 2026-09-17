"""
Semantic Resume Diff Service.

Compares two ResumeVersion JSON content payloads deterministically and structures
the differences section-by-section without exposing raw third-party jsondiff structures.
"""
from typing import Any, Dict, List, Optional
import json
import logging
from app.schemas.resume import (
    DiffSummary,
    EducationItemDiff,
    ExperienceItemDiff,
    ProjectItemDiff,
    ResumeDiffResponse,
    ResumeDiffSections,
    StringListDiff,
    TextDiff,
)
import uuid

logger = logging.getLogger(__name__)


def _parse_content(content: Any) -> Dict[str, Any]:
    """Parse resume content from string or dict safely."""
    if not content:
        return {}
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        try:
            return json.loads(content)
        except Exception:
            # If it's plain text rather than JSON, treat it as summary text
            return {"summary": content}
    return {}


def _diff_string_list(from_list: List[str], to_list: List[str]) -> StringListDiff:
    """Diff two lists of strings (e.g., skills). Order-independent, set-based."""
    s1 = [s.strip() for s in (from_list or []) if isinstance(s, str) and s.strip()]
    s2 = [s.strip() for s in (to_list or []) if isinstance(s, str) and s.strip()]

    set1 = set(s1)
    set2 = set(s2)

    added = [x for x in s2 if x not in set1]
    removed = [x for x in s1 if x not in set2]
    preserved = [x for x in s2 if x in set1]

    return StringListDiff(added=added, removed=removed, preserved=preserved)


def _diff_experience(
    from_exp: List[Dict[str, Any]], to_exp: List[Dict[str, Any]]
) -> tuple[List[ExperienceItemDiff], int, int, int]:
    """
    Compare experience entries.
    Matches primarily by (company, title).
    """
    items: List[ExperienceItemDiff] = []
    added_count = 0
    removed_count = 0
    changed_count = 0

    from_list = from_exp if isinstance(from_exp, list) else []
    to_list = to_exp if isinstance(to_exp, list) else []

    def make_key(item: Dict[str, Any], idx: int) -> str:
        comp = str(item.get("company", "")).strip().lower()
        title = str(item.get("title", "")).strip().lower()
        if comp or title:
            return f"{comp}::{title}"
        return f"item_{idx}"

    from_map: Dict[str, Dict[str, Any]] = {}
    for i, item in enumerate(from_list):
        if isinstance(item, dict):
            k = make_key(item, i)
            from_map[k] = item

    to_map: Dict[str, Dict[str, Any]] = {}
    for i, item in enumerate(to_list):
        if isinstance(item, dict):
            k = make_key(item, i)
            to_map[k] = item

    all_keys = list(from_map.keys())
    for k in to_map.keys():
        if k not in from_map:
            all_keys.append(k)

    for k in all_keys:
        in_from = k in from_map
        in_to = k in to_map

        if in_from and not in_to:
            f = from_map[k]
            bullets = f.get("bullets", [])
            items.append(
                ExperienceItemDiff(
                    key=k,
                    status="removed",
                    company=str(f.get("company", "")),
                    title=str(f.get("title", "")),
                    period_from=f.get("period"),
                    period_to=None,
                    location_from=f.get("location"),
                    location_to=None,
                    bullets_added=[],
                    bullets_removed=[str(b) for b in bullets if b],
                    bullets_preserved=[],
                )
            )
            removed_count += 1
        elif not in_from and in_to:
            t = to_map[k]
            bullets = t.get("bullets", [])
            items.append(
                ExperienceItemDiff(
                    key=k,
                    status="added",
                    company=str(t.get("company", "")),
                    title=str(t.get("title", "")),
                    period_from=None,
                    period_to=t.get("period"),
                    location_from=None,
                    location_to=t.get("location"),
                    bullets_added=[str(b) for b in bullets if b],
                    bullets_removed=[],
                    bullets_preserved=[],
                )
            )
            added_count += 1
        else:
            f = from_map[k]
            t = to_map[k]

            b_diff = _diff_string_list(f.get("bullets", []), t.get("bullets", []))

            period_changed = f.get("period") != t.get("period")
            loc_changed = f.get("location") != t.get("location")
            bullets_changed = bool(b_diff.added or b_diff.removed)

            is_modified = period_changed or loc_changed or bullets_changed
            status = "modified" if is_modified else "unchanged"

            if is_modified:
                changed_count += 1

            items.append(
                ExperienceItemDiff(
                    key=k,
                    status=status,
                    company=str(t.get("company", "") or f.get("company", "")),
                    title=str(t.get("title", "") or f.get("title", "")),
                    period_from=f.get("period"),
                    period_to=t.get("period"),
                    location_from=f.get("location"),
                    location_to=t.get("location"),
                    bullets_added=b_diff.added,
                    bullets_removed=b_diff.removed,
                    bullets_preserved=b_diff.preserved,
                )
            )

    return items, added_count, removed_count, changed_count


def _diff_projects(
    from_proj: List[Dict[str, Any]], to_proj: List[Dict[str, Any]]
) -> tuple[List[ProjectItemDiff], int, int, int]:
    """Compare projects by name."""
    items: List[ProjectItemDiff] = []
    added_count = 0
    removed_count = 0
    changed_count = 0

    from_list = from_proj if isinstance(from_proj, list) else []
    to_list = to_proj if isinstance(to_proj, list) else []

    def p_name(p: Dict[str, Any], idx: int) -> str:
        return str(p.get("name", "")).strip() or f"Project_{idx}"

    from_map = {p_name(p, i): p for i, p in enumerate(from_list) if isinstance(p, dict)}
    to_map = {p_name(p, i): p for i, p in enumerate(to_list) if isinstance(p, dict)}

    all_names = list(from_map.keys())
    for n in to_map.keys():
        if n not in from_map:
            all_names.append(n)

    for n in all_names:
        in_from = n in from_map
        in_to = n in to_map

        if in_from and not in_to:
            f = from_map[n]
            items.append(
                ProjectItemDiff(
                    name=n,
                    status="removed",
                    description_from=f.get("description"),
                    description_to=None,
                    url_from=f.get("url"),
                    url_to=None,
                )
            )
            removed_count += 1
        elif not in_from and in_to:
            t = to_map[n]
            items.append(
                ProjectItemDiff(
                    name=n,
                    status="added",
                    description_from=None,
                    description_to=t.get("description"),
                    url_from=None,
                    url_to=t.get("url"),
                )
            )
            added_count += 1
        else:
            f = from_map[n]
            t = to_map[n]
            desc_changed = f.get("description") != t.get("description")
            url_changed = f.get("url") != t.get("url")
            is_mod = desc_changed or url_changed
            status = "modified" if is_mod else "unchanged"
            if is_mod:
                changed_count += 1

            items.append(
                ProjectItemDiff(
                    name=n,
                    status=status,
                    description_from=f.get("description"),
                    description_to=t.get("description"),
                    url_from=f.get("url"),
                    url_to=t.get("url"),
                )
            )

    return items, added_count, removed_count, changed_count


def _diff_education(
    from_edu: List[Dict[str, Any]], to_edu: List[Dict[str, Any]]
) -> tuple[List[EducationItemDiff], int, int, int]:
    """Compare education entries by institution + degree."""
    items: List[EducationItemDiff] = []
    added_count = 0
    removed_count = 0
    changed_count = 0

    from_list = from_edu if isinstance(from_edu, list) else []
    to_list = to_edu if isinstance(to_edu, list) else []

    def make_key(e: Dict[str, Any], idx: int) -> str:
        inst = str(e.get("institution", "")).strip().lower()
        deg = str(e.get("degree", "")).strip().lower()
        return f"{inst}::{deg}" if (inst or deg) else f"edu_{idx}"

    from_map = {make_key(e, i): e for i, e in enumerate(from_list) if isinstance(e, dict)}
    to_map = {make_key(e, i): e for i, e in enumerate(to_list) if isinstance(e, dict)}

    all_keys = list(from_map.keys())
    for k in to_map.keys():
        if k not in from_map:
            all_keys.append(k)

    for k in all_keys:
        in_from = k in from_map
        in_to = k in to_map

        if in_from and not in_to:
            f = from_map[k]
            items.append(
                EducationItemDiff(
                    key=k,
                    status="removed",
                    institution=str(f.get("institution", "")),
                    degree=str(f.get("degree", "")),
                    field_of_study_from=f.get("field_of_study"),
                    field_of_study_to=None,
                    period_from=f.get("period"),
                    period_to=None,
                )
            )
            removed_count += 1
        elif not in_from and in_to:
            t = to_map[k]
            items.append(
                EducationItemDiff(
                    key=k,
                    status="added",
                    institution=str(t.get("institution", "")),
                    degree=str(t.get("degree", "")),
                    field_of_study_from=None,
                    field_of_study_to=t.get("field_of_study"),
                    period_from=None,
                    period_to=t.get("period"),
                )
            )
            added_count += 1
        else:
            f = from_map[k]
            t = to_map[k]
            fos_changed = f.get("field_of_study") != t.get("field_of_study")
            p_changed = f.get("period") != t.get("period")
            is_mod = fos_changed or p_changed
            status = "modified" if is_mod else "unchanged"
            if is_mod:
                changed_count += 1

            items.append(
                EducationItemDiff(
                    key=k,
                    status=status,
                    institution=str(t.get("institution", "") or f.get("institution", "")),
                    degree=str(t.get("degree", "") or f.get("degree", "")),
                    field_of_study_from=f.get("field_of_study"),
                    field_of_study_to=t.get("field_of_study"),
                    period_from=f.get("period"),
                    period_to=t.get("period"),
                )
            )

    return items, added_count, removed_count, changed_count


def compute_resume_diff(
    from_version_id: uuid.UUID,
    to_version_id: uuid.UUID,
    from_version_number: int,
    to_version_number: int,
    from_content_raw: Any,
    to_content_raw: Any,
) -> ResumeDiffResponse:
    """
    Compute structured semantic diff between two resume content payloads.
    """
    c_from = _parse_content(from_content_raw)
    c_to = _parse_content(to_content_raw)

    total_added = 0
    total_removed = 0
    total_changed = 0

    # 1. Summary diff
    sum_from = str(c_from.get("summary") or "").strip()
    sum_to = str(c_to.get("summary") or "").strip()
    sum_changed = sum_from != sum_to
    if sum_changed:
        if sum_from and not sum_to:
            total_removed += 1
        elif not sum_from and sum_to:
            total_added += 1
        else:
            total_changed += 1

    summary_diff = TextDiff(
        from_text=sum_from if sum_from else None,
        to_text=sum_to if sum_to else None,
        changed=sum_changed,
    )

    # 2. Skills diff
    skills_diff = _diff_string_list(c_from.get("skills", []), c_to.get("skills", []))
    total_added += len(skills_diff.added)
    total_removed += len(skills_diff.removed)

    # 3. Experience diff
    exp_diff, exp_add, exp_rem, exp_chg = _diff_experience(
        c_from.get("experience", []), c_to.get("experience", [])
    )
    total_added += exp_add
    total_removed += exp_rem
    total_changed += exp_chg

    # 4. Projects diff
    proj_diff, proj_add, proj_rem, proj_chg = _diff_projects(
        c_from.get("projects", []), c_to.get("projects", [])
    )
    total_added += proj_add
    total_removed += proj_rem
    total_changed += proj_chg

    # 5. Education diff
    edu_diff, edu_add, edu_rem, edu_chg = _diff_education(
        c_from.get("education", []), c_to.get("education", [])
    )
    total_added += edu_add
    total_removed += edu_rem
    total_changed += edu_chg

    has_changes = bool(total_added or total_removed or total_changed)

    return ResumeDiffResponse(
        from_version_id=from_version_id,
        to_version_id=to_version_id,
        from_version_number=from_version_number,
        to_version_number=to_version_number,
        has_changes=has_changes,
        summary=DiffSummary(
            added=total_added,
            removed=total_removed,
            changed=total_changed,
        ),
        sections=ResumeDiffSections(
            summary=summary_diff,
            skills=skills_diff,
            experience=exp_diff,
            projects=proj_diff,
            education=edu_diff,
        ),
    )
