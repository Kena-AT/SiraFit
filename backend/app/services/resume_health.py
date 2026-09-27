"""
Resume Health Score service.

Implements deterministic evaluation of resume / profile health across:
- Section completeness (25 pts)
- Action verb strength (25 pts)
- Quantified achievements ratio (25 pts)
- Formatting and bullet brevity (15 pts)
- Keyword & skill richness (10 pts)
Total score: 0-100.
"""

import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

STRONG_ACTION_VERBS = {
    "accelerated", "accomplished", "achieved", "acquired", "administered", "advised",
    "analyzed", "architected", "automated", "boosted", "built", "centralized",
    "championed", "coached", "collaborated", "conceived", "consolidated", "constructed",
    "converted", "created", "customized", "decreased", "delivered", "deployed",
    "designed", "developed", "devised", "directed", "doubled", "drove", "eliminated",
    "enabled", "engineered", "enhanced", "established", "exceeded", "executed",
    "expanded", "expedited", "fabricated", "facilitated", "formulated", "generated",
    "grew", "guided", "halved", "headed", "implemented", "improved", "increased",
    "initiated", "innovated", "inspected", "installed", "instituted", "integrated",
    "introduced", "invented", "launched", "lead", "led", "managed", "maximized",
    "mentored", "migrated", "minimized", "modernized", "negotiated", "optimized",
    "orchestrated", "outperformed", "overhauled", "oversaw", "partnered", "pioneered",
    "planned", "produced", "programmed", "promoted", "re-engineered", "rebuilt",
    "reduced", "refactored", "remodeled", "reorganized", "resolved", "restructured",
    "revamped", "saved", "scaled", "simplified", "spearheaded", "standardized",
    "streamlined", "strengthened", "surpassed", "synthesized", "trained", "transformed",
    "tripled", "unified", "upgraded", "yielded"
}

METRIC_REGEX = re.compile(
    r"(\b\d+(\.\d+)?%|\$\d+(\.\d+)?|\b\d+x\b|\b\d+\s*(users|customers|clients|requests|ms|seconds|minutes|hours|days|percent|million|k|M|B)\b|\+\d+)",
    re.IGNORECASE
)


class HealthCheckItem(BaseModel):
    category: str
    passed: bool
    score: int
    max_score: int
    title: str
    feedback: str


class ResumeHealthReport(BaseModel):
    overall_score: int
    grade: str
    summary: str
    breakdown: Dict[str, int]
    checks: List[HealthCheckItem]
    recommendations: List[str]

def calculate_profile_health(profile_input: Any) -> ResumeHealthReport:
    """Evaluate master profile or resume version health."""
    import json
    if isinstance(profile_input, str):
        try:
            profile_dict = json.loads(profile_input)
            if not isinstance(profile_dict, dict):
                profile_dict = {"summary": profile_input}
        except Exception:
            profile_dict = {"summary": profile_input}
    elif isinstance(profile_input, dict):
        profile_dict = profile_input
    else:
        profile_dict = {}

    checks: List[HealthCheckItem] = []
    recommendations: List[str] = []

    # 1. Section Completeness (Max 25)
    completeness_score = 0
    missing_sections = []

    if profile_dict.get("summary") and len(str(profile_dict.get("summary")).strip()) >= 50:
        completeness_score += 5
    else:
        missing_sections.append("Professional Summary (at least 50 characters)")

    if profile_dict.get("headline"):
        completeness_score += 4
    else:
        missing_sections.append("Headline / Title")

    exps = profile_dict.get("experiences") or profile_dict.get("experience") or []
    if len(exps) >= 1:
        completeness_score += 6
    else:
        missing_sections.append("Work Experience (at least 1 position)")

    skills = profile_dict.get("skills") or []
    if len(skills) >= 5:
        completeness_score += 5
    elif len(skills) > 0:
        completeness_score += 2
        missing_sections.append("Skills (add at least 5 key skills)")
    else:
        missing_sections.append("Skills")

    edus = profile_dict.get("educations") or profile_dict.get("education") or []
    if len(edus) >= 1:
        completeness_score += 5
    else:
        missing_sections.append("Education")

    completeness_passed = completeness_score >= 20
    checks.append(
        HealthCheckItem(
            category="completeness",
            passed=completeness_passed,
            score=completeness_score,
            max_score=25,
            title="Section Completeness",
            feedback=(
                "All essential resume sections are populated."
                if completeness_passed
                else f"Missing key sections: {', '.join(missing_sections)}"
            ),
        )
    )
    if missing_sections:
        recommendations.append(f"Complete missing sections: {', '.join(missing_sections)}.")

    # Gather all bullet points
    all_bullets: List[str] = []
    for exp in exps:
        b_list = exp.get("bullets")
        if isinstance(b_list, list):
            all_bullets.extend([str(b).strip() for b in b_list if str(b).strip()])
        elif exp.get("description"):
            # Split lines if description is plaintext
            lines = [l.strip("-* \t") for l in str(exp.get("description")).splitlines() if l.strip()]
            all_bullets.extend(lines)

    # 2. Action Verbs Strength (Max 25)
    action_verb_score = 0
    strong_bullets_count = 0
    if all_bullets:
        for b in all_bullets:
            first_word = re.sub(r"[^\w]", "", b.split()[0].lower()) if b.split() else ""
            if first_word in STRONG_ACTION_VERBS:
                strong_bullets_count += 1

        verb_ratio = strong_bullets_count / len(all_bullets)
        action_verb_score = min(25, int(verb_ratio * 30))  # 80%+ gets full 25
    else:
        action_verb_score = 5

    verb_passed = action_verb_score >= 18
    checks.append(
        HealthCheckItem(
            category="action_verbs",
            passed=verb_passed,
            score=action_verb_score,
            max_score=25,
            title="Action-Oriented Language",
            feedback=(
                f"{strong_bullets_count} of {len(all_bullets)} bullets start with high-impact action verbs."
                if all_bullets
                else "No experience bullet points provided."
            ),
        )
    )
    if not verb_passed:
        recommendations.append(
            "Start bullets with decisive action verbs (e.g., 'Spearheaded', 'Architected', 'Optimized', 'Deployed')."
        )

    # 3. Quantified Achievements (Max 25)
    quantified_count = 0
    if all_bullets:
        for b in all_bullets:
            if METRIC_REGEX.search(b):
                quantified_count += 1

        metric_ratio = quantified_count / len(all_bullets)
        quantified_score = min(25, int(metric_ratio * 35))  # ~70%+ gets full 25
    else:
        quantified_score = 5

    quantified_passed = quantified_score >= 18
    checks.append(
        HealthCheckItem(
            category="quantified_metrics",
            passed=quantified_passed,
            score=quantified_score,
            max_score=25,
            title="Quantified Impact & Metrics",
            feedback=(
                f"{quantified_count} of {len(all_bullets)} bullets include measurable metrics (%, $, time saved, users)."
                if all_bullets
                else "No measurable outcomes detected."
            ),
        )
    )
    if not quantified_passed:
        recommendations.append(
            "Quantify your accomplishments with concrete figures (e.g., 'increased throughput by 35%', 'saved $40k/yr')."
        )

    # 4. Formatting & Bullet Brevity (Max 15)
    formatting_score = 15
    formatting_feedback = []
    if all_bullets:
        for b in all_bullets:
            words = len(b.split())
            if words < 6:
                formatting_score = max(0, formatting_score - 2)
                formatting_feedback.append("Some bullets are too brief (< 6 words)")
                break
            elif words > 45:
                formatting_score = max(0, formatting_score - 2)
                formatting_feedback.append("Some bullets are overly verbose (> 45 words)")
                break
    else:
        formatting_score = 5

    formatting_passed = formatting_score >= 12
    checks.append(
        HealthCheckItem(
            category="formatting",
            passed=formatting_passed,
            score=formatting_score,
            max_score=15,
            title="Formatting & Brevity",
            feedback=(
                "Bullet lengths and density follow standard ATS guidelines."
                if formatting_passed
                else "; ".join(set(formatting_feedback)) or "Needs formatting balance."
            ),
        )
    )
    if not formatting_passed:
        recommendations.append("Keep each bullet between 12-30 words for optimal ATS parsing readability.")

    # 5. Skill Breadth & Richness (Max 10)
    skill_count = len(skills)
    skill_score = 10 if skill_count >= 10 else (6 if skill_count >= 5 else 3)
    skill_passed = skill_score >= 8
    checks.append(
        HealthCheckItem(
            category="skills_richness",
            passed=skill_passed,
            score=skill_score,
            max_score=10,
            title="Skill Breadth & Density",
            feedback=f"{skill_count} skills listed across technologies and methodologies.",
        )
    )
    if not skill_passed:
        recommendations.append("Include at least 8-12 core technical skills and tools.")

    total_score = min(
        100,
        completeness_score + action_verb_score + quantified_score + formatting_score + skill_score,
    )

    if total_score >= 90:
        grade = "A+"
        summary = "Exceptional resume health. Highly ATS-optimized with strong metrics and active voice."
    elif total_score >= 80:
        grade = "A"
        summary = "Strong resume profile. Well structured with good quantifiable outcomes."
    elif total_score >= 70:
        grade = "B"
        summary = "Solid foundation with a few high-impact optimization opportunities."
    elif total_score >= 60:
        grade = "C"
        summary = "Moderate health. Needs more quantified accomplishments and stronger action verbs."
    else:
        grade = "D"
        summary = "Significant gaps detected. Incomplete sections or lacking quantifiable achievements."

    return ResumeHealthReport(
        overall_score=total_score,
        grade=grade,
        summary=summary,
        breakdown={
            "completeness": completeness_score,
            "action_verbs": action_verb_score,
            "quantified_metrics": quantified_score,
            "formatting": formatting_score,
            "skills_richness": skill_score,
        },
        checks=checks,
        recommendations=recommendations,
    )


# Backward-compatible alias
calculate_resume_health = calculate_profile_health
