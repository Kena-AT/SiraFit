"""
Skill Taxonomy & Normalization Service (Sprint 2).

Provides canonical skill resolution, normalization, and taxonomy seeding.
Ensures skills stored in profiles resolve to controlled taxonomy identities.
"""
import re
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.models.skill_taxonomy import SkillTaxonomy


def normalize_skill_key(text: str) -> str:
    """
    Produce a canonical lookup key for a skill name.
    Normalizes case, whitespace, and common punctuation variations.
    e.g. "  Python " -> "python", "C++" -> "cpp", "React.js" -> "reactjs"
    """
    if not text:
        return ""
    cleaned = text.strip().lower()

    # Common symbol replacements (order matters: apply before generic cleanup)
    # Use re.sub without \b anchors since +, # are not word characters
    cleaned = re.sub(r"c\+\+", "cpp", cleaned)     # C++ -> cpp
    cleaned = re.sub(r"c#", "csharp", cleaned)       # C# -> csharp
    cleaned = re.sub(r"^\.net$", "dotnet", cleaned)  # .NET standalone -> dotnet
    cleaned = re.sub(r"\.net\b", "dotnet", cleaned)  # .NET prefix forms
    cleaned = re.sub(r"\.js\b", "js", cleaned)       # React.js -> Reactjs

    # Collapse spaces, hyphens, underscores, slashes
    cleaned = re.sub(r"[\s\-_/]+", "", cleaned)
    return cleaned


# Deterministic seed data for standard industry skills
DEFAULT_TAXONOMY = [
    # Languages
    {"key": "python", "name": "Python", "category": "Languages", "aliases": ["py", "python3", "python 3"]},
    {"key": "javascript", "name": "JavaScript", "category": "Languages", "aliases": ["js", "ecmascript", "es6"]},
    {"key": "typescript", "name": "TypeScript", "category": "Languages", "aliases": ["ts"]},
    {"key": "golang", "name": "Go", "category": "Languages", "aliases": ["golang"]},
    {"key": "rust", "name": "Rust", "category": "Languages", "aliases": ["rustlang"]},
    {"key": "java", "name": "Java", "category": "Languages", "aliases": ["java 11", "java 17", "java 21"]},
    {"key": "cpp", "name": "C++", "category": "Languages", "aliases": ["cplusplus", "cpp"]},
    {"key": "csharp", "name": "C#", "category": "Languages", "aliases": ["c-sharp", "c#", "csharp"]},
    {"key": "sql", "name": "SQL", "category": "Languages", "aliases": ["ansi sql", "structured query language"]},
    {"key": "html", "name": "HTML5", "category": "Languages", "aliases": ["html", "html 5"]},
    {"key": "css", "name": "CSS3", "category": "Languages", "aliases": ["css", "css 3", "stylesheets"]},
    {"key": "php", "name": "PHP", "category": "Languages", "aliases": ["php7", "php8"]},
    {"key": "ruby", "name": "Ruby", "category": "Languages", "aliases": ["ruby on rails language"]},

    # Frameworks & Libraries
    {"key": "react", "name": "React", "category": "Frameworks", "aliases": ["reactjs", "react.js"]},
    {"key": "nextjs", "name": "Next.js", "category": "Frameworks", "aliases": ["next", "next.js"]},
    {"key": "vuejs", "name": "Vue.js", "category": "Frameworks", "aliases": ["vue", "vuejs", "vue 3"]},
    {"key": "angular", "name": "Angular", "category": "Frameworks", "aliases": ["angularjs", "angular 2+"]},
    {"key": "django", "name": "Django", "category": "Frameworks", "aliases": ["django rest framework", "drf"]},
    {"key": "fastapi", "name": "FastAPI", "category": "Frameworks", "aliases": ["fast-api"]},
    {"key": "flask", "name": "Flask", "category": "Frameworks", "aliases": []},
    {"key": "expressjs", "name": "Express.js", "category": "Frameworks", "aliases": ["express", "expressjs"]},
    {"key": "nodejs", "name": "Node.js", "category": "Frameworks", "aliases": ["node", "nodejs"]},
    {"key": "springboot", "name": "Spring Boot", "category": "Frameworks", "aliases": ["spring", "spring framework"]},
    {"key": "tailwind", "name": "Tailwind CSS", "category": "Frameworks", "aliases": ["tailwind", "tailwindcss"]},

    # Databases
    {"key": "postgresql", "name": "PostgreSQL", "category": "Databases", "aliases": ["postgres", "psql"]},
    {"key": "mysql", "name": "MySQL", "category": "Databases", "aliases": []},
    {"key": "sqlite", "name": "SQLite", "category": "Databases", "aliases": ["sqlite3"]},
    {"key": "mongodb", "name": "MongoDB", "category": "Databases", "aliases": ["mongo"]},
    {"key": "redis", "name": "Redis", "category": "Databases", "aliases": []},
    {"key": "elasticsearch", "name": "Elasticsearch", "category": "Databases", "aliases": ["elastic", "es"]},

    # Cloud & DevOps
    {"key": "docker", "name": "Docker", "category": "DevOps", "aliases": ["containerization", "containers"]},
    {"key": "kubernetes", "name": "Kubernetes", "category": "DevOps", "aliases": ["k8s"]},
    {"key": "aws", "name": "AWS", "category": "DevOps", "aliases": ["amazon web services"]},
    {"key": "gcp", "name": "Google Cloud", "category": "DevOps", "aliases": ["gcp", "google cloud platform"]},
    {"key": "azure", "name": "Microsoft Azure", "category": "DevOps", "aliases": ["azure"]},
    {"key": "git", "name": "Git", "category": "DevOps", "aliases": ["github", "gitlab"]},
    {"key": "cicd", "name": "CI/CD", "category": "DevOps", "aliases": ["continuous integration", "github actions", "jenkins"]},
    {"key": "terraform", "name": "Terraform", "category": "DevOps", "aliases": ["tf", "iac"]},
    {"key": "linux", "name": "Linux", "category": "DevOps", "aliases": ["bash", "unix", "shell scripting"]},

    # Practices & Methodologies
    {"key": "restapi", "name": "RESTful APIs", "category": "Methodologies", "aliases": ["rest", "rest api", "restful api"]},
    {"key": "graphql", "name": "GraphQL", "category": "Methodologies", "aliases": []},
    {"key": "agile", "name": "Agile", "category": "Methodologies", "aliases": ["scrum", "kanban"]},
    {"key": "systemdesign", "name": "System Design", "category": "Methodologies", "aliases": ["software architecture", "distributed systems"]},
    {"key": "testing", "name": "Unit Testing", "category": "Methodologies", "aliases": ["tdd", "pytest", "jest", "automated testing"]},
]


def seed_skill_taxonomy(db: Session) -> int:
    """
    Idempotently seed the SkillTaxonomy table with default entries.
    Returns the number of new entries created.
    """
    created_count = 0
    for item in DEFAULT_TAXONOMY:
        existing = (
            db.query(SkillTaxonomy)
            .filter(
                (SkillTaxonomy.canonical_key == item["key"])
                | (SkillTaxonomy.name == item["name"])
            )
            .first()
        )
        if not existing:
            entry = SkillTaxonomy(
                canonical_key=item["key"],
                name=item["name"],
                category=item["category"],
                aliases=item["aliases"],
                active=True,
            )
            db.add(entry)
            created_count += 1
    if created_count > 0:
        db.commit()
    return created_count


def resolve_skill(name: str, db: Session) -> Optional[dict[str, Any]]:
    """
    Resolve an arbitrary skill name against the canonical taxonomy.
    Matches via exact name, canonical key, or configured aliases.
    """
    if not name or not name.strip():
        return None

    raw_name = name.strip()
    norm_key = normalize_skill_key(raw_name)

    # 1. Direct canonical_key match
    taxonomy_match = (
        db.query(SkillTaxonomy)
        .filter(SkillTaxonomy.canonical_key == norm_key, SkillTaxonomy.active == True)
        .first()
    )
    if taxonomy_match:
        return {
            "name": taxonomy_match.name,
            "canonical_key": taxonomy_match.canonical_key,
            "category": taxonomy_match.category,
        }

    # 2. Case-insensitive exact name match
    taxonomy_match = (
        db.query(SkillTaxonomy)
        .filter(SkillTaxonomy.name.ilike(raw_name), SkillTaxonomy.active == True)
        .first()
    )
    if taxonomy_match:
        return {
            "name": taxonomy_match.name,
            "canonical_key": taxonomy_match.canonical_key,
            "category": taxonomy_match.category,
        }

    # 3. Check aliases in all active taxonomy entries
    all_taxonomies = db.query(SkillTaxonomy).filter(SkillTaxonomy.active == True).all()
    for t in all_taxonomies:
        aliases = t.aliases or []
        for alias in aliases:
            if alias.lower() == raw_name.lower() or normalize_skill_key(alias) == norm_key:
                return {
                    "name": t.name,
                    "canonical_key": t.canonical_key,
                    "category": t.category,
                }

    return None


def canonicalize_profile_skills(skills: list[dict[str, Any]], db: Session) -> list[dict[str, Any]]:
    """
    Normalize and canonicalize a list of skills before persisting.
    - Resolves known skills to canonical taxonomy name and category.
    - Dedeplicates skills that resolve to the same canonical key.
    - Preserves unmapped skills with original name (no data loss).
    """
    result = []
    seen_keys: set[str] = set()

    for s in skills:
        raw_name = (s.get("name") or "").strip()
        if not raw_name:
            continue

        resolved = resolve_skill(raw_name, db)
        if resolved:
            key = resolved["canonical_key"]
            if key in seen_keys:
                continue
            seen_keys.add(key)
            result.append({
                "name": resolved["name"],
                "category": s.get("category") or resolved["category"],
                "proficiency": s.get("proficiency"),
            })
        else:
            raw_key = normalize_skill_key(raw_name)
            if raw_key in seen_keys:
                continue
            seen_keys.add(raw_key)
            result.append({
                "name": raw_name,
                "category": s.get("category"),
                "proficiency": s.get("proficiency"),
            })

    return result
