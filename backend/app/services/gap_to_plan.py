from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.profile import Profile
from app.models.job import Job
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.learning_resource import LearningResource
from app.models.project_template import ProjectTemplate


def generate_learning_plan(db: Session, profile: Profile, job: Job) -> Dict[str, Any]:
    """
    Generates a deterministic learning plan based on skill gaps.
    No LLM is used here; strictly mapping missing skills to registered resources.
    """
    # 1. Determine skill gap (deterministic)
    profile_skills = (
        {skill.name.lower() for skill in profile.skills} if profile.skills else set()
    )
    job_tags = set(job.tags) if job.tags else set()

    missing_skill_names = [tag for tag in job_tags if tag.lower() not in profile_skills]

    if not missing_skill_names:
        return {"missing_skills": [], "plan_items": []}

    # Normalize missing skills to canonical keys to query learning resources
    # Here we assume tags are close to canonical_keys or we find the taxonomy record
    # For robust matching, we look up taxonomy by name (lowered) or canonical_key
    stmt = select(SkillTaxonomy).where(
        SkillTaxonomy.name.in_(missing_skill_names)
        | SkillTaxonomy.canonical_key.in_(
            [s.lower().replace(" ", "-") for s in missing_skill_names]
        )
    )
    taxonomy_skills = db.execute(stmt).scalars().all()

    # Fallback: if some skills aren't in taxonomy, we just use their lowercase form as canonical_key
    canonical_keys = [s.canonical_key for s in taxonomy_skills]
    for ms in missing_skill_names:
        fallback_key = ms.lower().replace(" ", "-")
        if fallback_key not in canonical_keys:
            canonical_keys.append(fallback_key)

    # 2. Query Curated Registry (Learning Resources & Project Templates)
    resources_stmt = select(LearningResource).where(
        LearningResource.skill_id.in_(canonical_keys),
        LearningResource.is_active == True,
    )
    resources = db.execute(resources_stmt).scalars().all()

    # For projects, skill_ids is a JSON array. We need to check if any canonical key overlaps.
    # In SQLite JSON operations are limited, but we can fetch active projects and filter in python for now.
    projects_stmt = select(ProjectTemplate).where(ProjectTemplate.is_active == True)
    all_projects = db.execute(projects_stmt).scalars().all()

    projects = []
    for p in all_projects:
        if set(p.skill_ids).intersection(canonical_keys):
            projects.append(p)

    # 3. Synthesize Plan
    plan_items = []

    for resource in resources:
        plan_items.append(
            {
                "type": "learning_resource",
                "id": str(resource.id),
                "skill_id": resource.skill_id,
                "title": resource.title,
                "provider": resource.provider,
                "resource_type": resource.resource_type,
                "difficulty": resource.difficulty,
                "estimated_minutes": resource.estimated_minutes,
                "url": resource.url,
            }
        )

    for project in projects:
        plan_items.append(
            {
                "type": "project_template",
                "id": str(project.id),
                "skills": project.skill_ids,
                "title": project.title,
                "difficulty": project.difficulty,
                "estimated_minutes": project.estimated_minutes,
            }
        )

    return {"missing_skills": missing_skill_names, "plan_items": plan_items}
