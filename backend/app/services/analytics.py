"""
Analytics service for generating metrics, snapshots, and Excel exports.
Sprint 10: Salary Benchmarks, Skills Gap, and Application Stall Insights.
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
import io
import math
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models.analytics import AnalyticsSnapshot
from app.models.job import ApplicationEvent, Job, JobAnalysis, JobApplication
from app.models.profile import Profile
from app.models.skill_taxonomy import SkillTaxonomy
from app.services.skill_taxonomy import normalize_skill_key, resolve_skill


def _utcnow():
    return datetime.now(timezone.utc)


def _percentile(values: List[float], p: float) -> Optional[float]:
    """Compute percentile p in [0, 1] using standard linear interpolation."""
    if not values:
        return None
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 1:
        return float(sorted_vals[0])
    idx = p * (n - 1)
    lower = int(math.floor(idx))
    upper = int(math.ceil(idx))
    weight = idx - lower
    return float(sorted_vals[lower] * (1.0 - weight) + sorted_vals[upper] * weight)


def normalize_job_role(title: str) -> str:
    """
    Map raw job titles into stable canonical role families.
    Strips seniority indicators and maps common variations.
    e.g. "Senior Backend Software Engineer" -> "Backend Engineer"
    """
    if not title or not title.strip():
        return "Software Engineer"

    # Strip seniority words
    cleaned = re.sub(
        r"\b(senior|junior|staff|principal|lead|mid|associate|sr\.|jr\.|head of|director|intern|vp|lead)\b",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(r"[\s\-_/]+", " ", cleaned).strip().lower()

    # Domain role matching (specific data roles prioritized over generic platform)
    if any(
        k in cleaned for k in ["data engineer", "data platform", "data pipeline", "etl"]
    ):
        return "Data Engineer"
    if any(
        k in cleaned
        for k in [
            "data scientist",
            "machine learning",
            "ml engineer",
            "ai engineer",
            "deep learning",
        ]
    ):
        return "AI / ML Engineer"
    if any(k in cleaned for k in ["backend", "back-end", "back end", "server"]):
        return "Backend Engineer"
    if any(
        k in cleaned
        for k in ["frontend", "front-end", "front end", "ui/ux engineer", "ui engineer"]
    ):
        return "Frontend Engineer"
    if any(k in cleaned for k in ["fullstack", "full stack", "full-stack"]):
        return "Full Stack Engineer"
    if any(
        k in cleaned
        for k in [
            "devops",
            "site reliability",
            "sre",
            "platform engineer",
            "infrastructure",
            "cloud engineer",
        ]
    ):
        return "DevOps Engineer"
        return "AI / ML Engineer"
    if any(
        k in cleaned for k in ["qa", "test", "quality assurance", "automation engineer"]
    ):
        return "QA Engineer"
    if any(
        k in cleaned for k in ["mobile", "ios", "android", "flutter", "react native"]
    ):
        return "Mobile Engineer"
    if any(k in cleaned for k in ["product manager", "product owner", "pm"]):
        return "Product Manager"
    if any(k in cleaned for k in ["security", "infosec", "cybersecurity"]):
        return "Security Engineer"
    if any(k in cleaned for k in ["designer", "ui/ux", "product designer"]):
        return "Product Designer"
    if any(
        k in cleaned
        for k in ["engineering manager", "technical manager", "dev manager"]
    ):
        return "Engineering Manager"

    # Fallback to normalized title
    fallback = cleaned.title()
    return fallback if fallback else "Software Engineer"


def compute_salary_benchmarks(jobs: List[Job]) -> List[Dict[str, Any]]:
    """
    Compute market salary percentile distributions from eligible jobs.
    Segregates strictly by (role, currency, period).
    Enforces minimum sample threshold (SALARY_BENCHMARK_MIN_SAMPLES = 5).
    """
    groups: Dict[Tuple[str, str, str], Dict[str, List[float]]] = defaultdict(
        lambda: {"mins": [], "maxs": [], "records": 0}
    )

    for job in jobs:
        # Currency: standard 3-letter code (default to USD if not specified)
        curr = (job.currency or "USD").upper().strip()
        period = "annual"  # Default pay period

        # Validate salary fields
        s_min = job.salary_min
        s_max = job.salary_max

        # Exclude invalid records
        if s_min is None and s_max is None:
            continue
        if s_min is not None and s_max is not None and s_min > s_max:
            continue
        if s_min is not None and s_min <= 0:
            continue
        if s_max is not None and s_max <= 0:
            continue

        role = normalize_job_role(job.title or "")
        key = (role, curr, period)
        groups[key]["records"] += 1

        if s_min is not None:
            groups[key]["mins"].append(float(s_min))
        if s_max is not None:
            groups[key]["maxs"].append(float(s_max))

    benchmarks: List[Dict[str, Any]] = []
    min_samples = getattr(settings, "SALARY_BENCHMARK_MIN_SAMPLES", 5)

    for (role, currency, period), data in sorted(
        groups.items(), key=lambda x: x[1]["records"], reverse=True
    ):
        sample_size = data["records"]
        mins = data["mins"]
        maxs = data["maxs"]

        if sample_size >= min_samples:
            min_p50 = _percentile(mins, 0.50) if mins else None
            max_p50 = _percentile(maxs, 0.50) if maxs else None
            min_p25 = _percentile(mins, 0.25) if mins else None
            max_p75 = _percentile(maxs, 0.75) if maxs else None
        else:
            min_p50 = None
            max_p50 = None
            min_p25 = None
            max_p75 = None

        benchmarks.append(
            {
                "role": role,
                "currency": currency,
                "period": period,
                "sample_size": sample_size,
                "min_p50": round(min_p50, 2) if min_p50 is not None else None,
                "max_p50": round(max_p50, 2) if max_p50 is not None else None,
                "min_p25": round(min_p25, 2) if min_p25 is not None else None,
                "max_p75": round(max_p75, 2) if max_p75 is not None else None,
            }
        )

    return benchmarks[: getattr(settings, "SALARY_BENCHMARK_MAX_ROLES", 10)]


def compute_skills_gap(
    db: Session,
    user_id: uuid.UUID,
    jobs: List[Job],
) -> Dict[str, Any]:
    """
    Compare canonical job-required skills against user's canonical profile skills.
    Deduplicates skills per job and resolves taxonomy aliases.
    Excludes skills present in profile.
    """
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    # Build canonical set of user profile skills
    user_skill_keys: set[str] = set()
    current_skill_count = 0
    if profile and profile.skills:
        current_skill_count = len(profile.skills)
        for s in profile.skills:
            if not s.name:
                continue
            resolved = resolve_skill(s.name, db)
            if resolved:
                user_skill_keys.add(resolved["canonical_key"])
            else:
                user_skill_keys.add(normalize_skill_key(s.name))

    analyzed_jobs_count = len(jobs)
    skill_frequency: Counter[Tuple[str, str, Optional[str]]] = Counter()

    # Pre-fetch job analyses to avoid N+1 queries
    job_ids = [j.id for j in jobs]
    job_analyses = (
        db.query(JobAnalysis).filter(JobAnalysis.job_id.in_(job_ids)).all()
        if job_ids
        else []
    )
    analysis_by_job_id = {a.job_id: a for a in job_analyses}

    # Extract required skills per job (deduplicated per job)
    for job in jobs:
        job_seen_keys: set[str] = set()

        # Source 1: Job tags
        raw_skills: List[str] = []
        if job.tags and isinstance(job.tags, list):
            raw_skills.extend(job.tags)

        # Source 2: JobAnalysis key_requirements & key required skills
        analysis = analysis_by_job_id.get(job.id)
        if analysis:
            if analysis.key_requirements and isinstance(
                analysis.key_requirements, list
            ):
                raw_skills.extend(analysis.key_requirements)

        for raw_s in raw_skills:
            if not isinstance(raw_s, str) or not raw_s.strip():
                continue
            # Some key_requirements may be full phrases; if it's short (< 40 chars), treat as skill
            s_candidate = raw_s.strip()
            if len(s_candidate) > 45:
                continue

            resolved = resolve_skill(s_candidate, db)
            if resolved:
                c_key = resolved["canonical_key"]
                c_name = resolved["name"]
                c_category = resolved.get("category", "General")
            else:
                c_key = normalize_skill_key(s_candidate)
                c_name = s_candidate.title()
                c_category = "General"

            if not c_key or c_key in job_seen_keys:
                continue
            job_seen_keys.add(c_key)

            # Skip if user already has this skill
            if c_key in user_skill_keys:
                continue

            skill_frequency[(c_key, c_name, c_category)] += 1

    skills_gap_items: List[Dict[str, Any]] = []
    threshold = getattr(settings, "SKILLS_GAP_PRIORITY_THRESHOLD", 0.20)

    # Sort by frequency descending, then name ascending
    sorted_skills = sorted(
        skill_frequency.items(),
        key=lambda x: (x[1], x[0][1]),
        reverse=True,
    )

    top_n = getattr(settings, "SKILLS_GAP_TOP_N", 15)
    for (c_key, c_name, c_category), freq in sorted_skills[:top_n]:
        pct = (freq / analyzed_jobs_count * 100.0) if analyzed_jobs_count > 0 else 0.0
        priority = pct >= (threshold * 100.0)

        # Look up taxonomy ID if it exists
        tax = (
            db.query(SkillTaxonomy).filter(SkillTaxonomy.canonical_key == c_key).first()
        )
        skill_id = str(tax.id) if tax else None

        skills_gap_items.append(
            {
                "skill_id": skill_id,
                "skill": c_name,
                "frequency": freq,
                "percentage": round(pct, 1),
                "priority": priority,
            }
        )

    return {
        "analyzed_jobs": analyzed_jobs_count,
        "current_skill_count": current_skill_count,
        "skills": skills_gap_items,
    }


def compute_stall_insights(
    db: Session,
    user_id: uuid.UUID,
    applications: List[JobApplication],
) -> Dict[str, Any]:
    """
    Derive stage durations and drop-off metrics from actual status transitions.
    Uses ApplicationEvent (event_type == 'status_change') ordered chronologically.
    Avoids N+1 queries by batch loading events for all applications.
    """
    total_apps = len(applications)
    if not total_apps:
        return {
            "total_applications": 0,
            "stages": [],
            "longest_median_stage": None,
            "highest_drop_off_stage": None,
        }

    # Canonical linear pipeline stages
    PIPELINE_STAGES = ["applied", "screening", "interview", "final_round", "offer"]
    TERMINAL_STAGES = {"rejected", "withdrawn", "archived"}

    # Batch query status_change events for all user applications
    app_ids = [a.id for a in applications]
    events = (
        db.query(ApplicationEvent)
        .filter(
            ApplicationEvent.application_id.in_(app_ids),
            ApplicationEvent.event_type.in_(["status_change", "status_transition"]),
        )
        .order_by(ApplicationEvent.application_id, ApplicationEvent.occurred_at.asc())
        .all()
    )

    events_by_app: Dict[uuid.UUID, List[ApplicationEvent]] = defaultdict(list)
    for ev in events:
        events_by_app[ev.application_id].append(ev)

    # Per-stage aggregators
    stage_entered: Counter[str] = Counter()
    stage_progressed: Counter[str] = Counter()
    stage_dropped: Counter[str] = Counter()
    stage_durations_hours: Dict[str, List[float]] = defaultdict(list)

    # Process each application's transition history
    for app in applications:
        app_events = events_by_app.get(app.id, [])

        # If no status_change events recorded (e.g. created directly with a status),
        # infer entry into app.status at app.created_at
        if not app_events:
            curr_st = (app.status or "applied").lower()
            if curr_st in PIPELINE_STAGES:
                stage_entered[curr_st] += 1
            continue

        # Extract sequence of (stage, timestamp)
        transitions: List[Tuple[str, datetime]] = []
        for ev in app_events:
            meta = ev.event_metadata or {}
            to_st = meta.get("to_status")
            if not to_st:
                # Fallback: check event description or title
                m = re.search(
                    r"(?:to|changed to)\s+([a-zA-Z_]+)", ev.title or "", re.IGNORECASE
                )
                to_st = m.group(1).lower() if m else None
            if to_st:
                transitions.append((to_st.lower(), ev.occurred_at))

        # Reconstruct timeline including initial state if first transition occurred later
        if transitions:
            first_from = (app_events[0].event_metadata or {}).get("from_status")
            if first_from and first_from.lower() in PIPELINE_STAGES:
                entry_time = app.created_at or transitions[0][1]
                transitions.insert(0, (first_from.lower(), entry_time))

        # Analyze stage entry, progression, drop-off, and duration
        for i, (stage, entered_at) in enumerate(transitions):
            if stage not in PIPELINE_STAGES:
                continue

            stage_entered[stage] += 1

            # Has next transition?
            if i + 1 < len(transitions):
                next_stage, next_time = transitions[i + 1]
                duration_hours = max(
                    0.0, (next_time - entered_at).total_seconds() / 3600.0
                )
                stage_durations_hours[stage].append(duration_hours)

                if next_stage in TERMINAL_STAGES:
                    stage_dropped[stage] += 1
                else:
                    stage_progressed[stage] += 1
            else:
                # Current/terminal state without subsequent transition
                curr_status = (app.status or "").lower()
                if curr_status in TERMINAL_STAGES:
                    stage_dropped[stage] += 1
                # Otherwise still active in this stage (censored)

    stage_insights: List[Dict[str, Any]] = []
    min_median_apps = getattr(settings, "STAGE_MEDIAN_MIN_APPLICATIONS", 3)

    longest_stage: Optional[str] = None
    longest_hours: float = -1.0

    highest_drop_stage: Optional[str] = None
    highest_drop_rate: float = -1.0

    for stage in PIPELINE_STAGES:
        entered = stage_entered[stage]
        progressed = stage_progressed[stage]
        dropped = stage_dropped[stage]
        durations = stage_durations_hours[stage]
        sample_size = len(durations)

        drop_off_rate = (dropped / entered) if entered > 0 else None

        if sample_size >= min_median_apps:
            median_hours = _percentile(durations, 0.50)
        else:
            median_hours = None

        if median_hours is not None and median_hours > longest_hours:
            longest_hours = median_hours
            longest_stage = stage

        if (
            drop_off_rate is not None
            and drop_off_rate > highest_drop_rate
            and entered > 0
        ):
            highest_drop_rate = drop_off_rate
            highest_drop_stage = stage

        stage_insights.append(
            {
                "stage": stage,
                "entered_count": entered,
                "progressed_count": progressed,
                "dropped_count": dropped,
                "drop_off_rate": round(drop_off_rate, 3)
                if drop_off_rate is not None
                else None,
                "median_duration_hours": round(median_hours, 1)
                if median_hours is not None
                else None,
                "duration_sample_size": sample_size,
            }
        )

    return {
        "total_applications": total_apps,
        "stages": stage_insights,
        "longest_median_stage": longest_stage,
        "highest_drop_off_stage": highest_drop_stage,
    }


def generate_analytics_metrics(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
    """
    Generate comprehensive analytics metrics for a user.
    Maintains full backward compatibility while introducing Sprint 10 expansion fields.
    """
    # 1. Application metrics - eager load Job relationship to avoid N+1
    applications = (
        db.query(JobApplication)
        .filter(JobApplication.user_id == user_id)
        .options(joinedload(JobApplication.job))
        .all()
    )
    total_applications = len(applications)

    # Weekly application trend calculation
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)
    apps_this_week = 0
    apps_last_week = 0
    for app in applications:
        if app.created_at:
            c_at = app.created_at if app.created_at.tzinfo else app.created_at.replace(tzinfo=timezone.utc)
            if c_at >= seven_days_ago:
                apps_this_week += 1
            elif c_at >= fourteen_days_ago:
                apps_last_week += 1

    diff = apps_this_week - apps_last_week
    if diff > 0:
        applications_trend = f"+{diff} this week"
    elif diff < 0:
        applications_trend = f"{diff} this week"
    elif apps_this_week > 0:
        applications_trend = f"+{apps_this_week} this week"
    else:
        applications_trend = "+0 this week"

    # Interview stages
    interview_stages = ["screening", "interview", "final_round"]
    interviewed = sum(1 for a in applications if a.status in interview_stages)
    interview_rate = (
        (interviewed / total_applications * 100) if total_applications > 0 else 0
    )

    # Offer rate
    offers = sum(1 for a in applications if a.status == "offer")
    offer_rate = (offers / total_applications * 100) if total_applications > 0 else 0

    # Average response time (for applications that got a response)
    response_times = []
    for app in applications:
        if app.updated_at and app.created_at:
            diff = app.updated_at - app.created_at
            response_times.append(diff.total_seconds() / 86400)  # days
    avg_response_time = (
        sum(response_times) / len(response_times) if response_times else 0
    )

    # 2. Conversion funnel (legacy view)
    funnel_stages = [
        ("Applied", "applied"),
        ("Recruiter screen", "screening"),
        ("Tech screen", "interview"),
        ("Onsite / final", "final_round"),
        ("Offer", "offer"),
    ]
    funnel = []
    for label, status in funnel_stages:
        count = sum(
            1
            for a in applications
            if a.status == status or (status == "applied" and a.status == "applied")
        )
        funnel.append({"stage": label, "count": count})

    # 3. Rejection stages
    rejection_stages = [
        ("Resume screen", "resume_screen"),
        ("Recruiter call", "recruiter_call"),
        ("Tech screen", "tech_screen"),
        ("Onsite", "onsite"),
        ("Offer declined", "offer_declined"),
    ]
    rejections = []
    for label, stage in rejection_stages:
        count = sum(
            1
            for a in applications
            if a.status == "rejected" and a.rejection_stage == stage
        )
        rejections.append({"stage": label, "count": count})

    # 4. Skill coverage vs market demand
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    user_skills = set(s.name.lower() for s in profile.skills) if profile else set()

    job_ids = [a.job_id for a in applications]
    all_job_skills = set()
    skill_job_counts: Dict[str, int] = {}
    applied_jobs: List[Job] = []
    if job_ids:
        applied_jobs = db.query(Job).filter(Job.id.in_(job_ids)).all()
        for job in applied_jobs:
            if job.tags:
                for tag in job.tags:
                    tag_lower = tag.lower()
                    all_job_skills.add(tag_lower)
                    skill_job_counts[tag_lower] = skill_job_counts.get(tag_lower, 0) + 1

    total_applied_with_skills = len(applied_jobs) if job_ids else 0
    skill_coverage = []
    for skill in all_job_skills:
        you = 100 if skill in user_skills else 0
        market = int(
            skill_job_counts.get(skill, 0) / max(1, total_applied_with_skills) * 100
        )
        skill_coverage.append(
            {
                "skill": skill.title(),
                "you": you,
                "market": market,
            }
        )

    # 5. Market demand - aggregated from the jobs imported/applied
    title_counter: Counter[str] = Counter()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)
    recent_roles: Counter[str] = Counter()
    prior_roles: Counter[str] = Counter()

    for job in applied_jobs:
        normalised = normalize_job_role(job.title)
        if normalised:
            title_counter[normalised] += 1
            job_time = job.created_at or job.posted_at
            if job_time:
                jt = job_time if job_time.tzinfo else job_time.replace(tzinfo=timezone.utc)
                if jt >= thirty_days_ago:
                    recent_roles[normalised] += 1
                elif jt >= sixty_days_ago:
                    prior_roles[normalised] += 1

    top_roles = title_counter.most_common(8)
    market_demand = []

    for role, count in top_roles:
        demand = min(100, count * 10)
        recent_count = recent_roles.get(role, 0)
        prior_count = prior_roles.get(role, 0)
        if prior_count > 0:
            pct = ((recent_count - prior_count) / prior_count) * 100
            change_str = f"+{pct:.1f}%" if pct >= 0 else f"{pct:.1f}%"
        elif recent_count > 0:
            change_str = f"+{recent_count * 10.0:.1f}%"
        else:
            change_str = "+0.0%"

        market_demand.append(
            {
                "role": role,
                "demand": demand,
                "postings": count,
                "change": change_str,
            }
        )

    # 6. Top technologies
    skill_counter: Counter[str] = Counter()
    for app in applications:
        if app.job and app.job.tags:
            for tag in app.job.tags:
                skill_counter[tag.lower()] += 1

    top_technologies = [
        {"skill": skill.title(), "count": count}
        for skill, count in skill_counter.most_common(10)
    ]

    # 7. Legacy salary medians by sector/company
    salary_data = (
        db.query(Job)
        .join(JobApplication)
        .filter(
            JobApplication.user_id == user_id,
            Job.salary_min.isnot(None),
            Job.salary_max.isnot(None),
        )
        .all()
    )
    company_salaries: Dict[str, List[float]] = defaultdict(list)
    for j in salary_data:
        company_salaries[j.company].append(float((j.salary_min + j.salary_max) / 2))

    salary_medians = {
        company: round(sum(sals) / len(sals), 1)
        for company, sals in company_salaries.items()
    }

    # 8. Legacy skill gaps
    legacy_gaps = []
    for skill, freq in skill_counter.most_common(10):
        if skill not in user_skills:
            legacy_gaps.append(
                {
                    "skill": skill.title(),
                    "demand_frequency": freq,
                    "impact_score": min(freq * 10, 100),
                }
            )

    # -----------------------------------------------------------------------
    # Sprint 10 Expansions
    # -----------------------------------------------------------------------
    # Jobs pool for benchmark and skills-gap analysis (user's applied and imported jobs)
    all_user_jobs = list({app.job for app in applications if app.job})

    # 9. Salary Benchmarks
    salary_benchmarks = compute_salary_benchmarks(all_user_jobs)

    # 10. Canonical Skills Gap
    skills_gap_response = compute_skills_gap(db, user_id, all_user_jobs)

    # 11. Application Stall Insights
    stall_insights_response = compute_stall_insights(db, user_id, applications)

    return {
        "total_applications": total_applications,
        "applications_this_week": apps_this_week,
        "applications_last_week": apps_last_week,
        "applications_trend": applications_trend,
        "interview_rate": round(interview_rate, 1),
        "avg_response_time_days": round(avg_response_time, 1),
        "offer_rate": round(offer_rate, 1),
        "conversion_funnel": funnel,
        "rejection_stages": rejections,
        "skill_coverage": skill_coverage,
        "market_demand": market_demand,
        "top_technologies": top_technologies,
        "salary_medians": salary_medians,
        "skill_gaps": legacy_gaps,
        # Sprint 10
        "salary_benchmarks": salary_benchmarks,
        "skills_gap_analysis": skills_gap_response,
        "stall_insights": stall_insights_response,
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_analytics_excel(metrics: Dict[str, Any]) -> bytes:
    """
    Export analytics into a clean, multi-tab Excel (.xlsx) workbook.
    Sheets:
      1. Overview
      2. Salary Benchmarks
      3. Skills Gap
      4. Stall Insights
      5. Conversion Funnel
    Consumes identical metrics dictionary to guarantee zero divergence.
    """
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Styles
    header_fill = PatternFill(
        start_color="1E293B", end_color="1E293B", fill_type="solid"
    )
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    cell_font = Font(name="Segoe UI", size=10)
    title_font = Font(name="Segoe UI", size=14, bold=True, color="0F172A")
    subtitle_font = Font(name="Segoe UI", size=9, italic=True, color="64748B")
    border_side = Side(style="thin", color="E2E8F0")
    cell_border = Border(
        left=border_side, right=border_side, top=border_side, bottom=border_side
    )

    # Helper for formatting header row
    def style_header(ws, row_idx, headers):
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = cell_border

    # 1. Overview Sheet
    ws_overview = wb.create_sheet("Overview")
    ws_overview.cell(
        row=1, column=1, value="SiraFit Analytics Report"
    ).font = title_font
    ws_overview.cell(
        row=2, column=1, value=f"Generated: {metrics.get('generated_at', '')}"
    ).font = subtitle_font

    style_header(ws_overview, 4, ["Metric", "Value", "Unit / Context"])
    overview_rows = [
        (
            "Total Applications",
            metrics.get("total_applications", 0),
            "Tracked applications",
        ),
        (
            "Interview Rate",
            f"{metrics.get('interview_rate', 0)}%",
            "Applications reaching screening/interview",
        ),
        (
            "Offer Rate",
            f"{metrics.get('offer_rate', 0)}%",
            "Applications receiving an offer",
        ),
        (
            "Average Response Time",
            f"{metrics.get('avg_response_time_days', 0)}",
            "Days from applied to last update",
        ),
    ]
    for r_idx, (k, v, desc) in enumerate(overview_rows, 5):
        ws_overview.cell(row=r_idx, column=1, value=k).font = cell_font
        ws_overview.cell(row=r_idx, column=2, value=v).font = cell_font
        ws_overview.cell(row=r_idx, column=3, value=desc).font = cell_font
        for c_idx in range(1, 4):
            ws_overview.cell(row=r_idx, column=c_idx).border = cell_border

    # 2. Salary Benchmarks Sheet
    ws_salary = wb.create_sheet("Salary Benchmarks")
    ws_salary.cell(row=1, column=1, value="Market Salary Benchmarks").font = title_font
    ws_salary.cell(
        row=2,
        column=1,
        value="Calculated from comparable imported jobs with valid salary metadata (min 5 samples required for percentiles)",
    ).font = subtitle_font

    salary_headers = [
        "Role",
        "Currency",
        "Period",
        "Sample Size",
        "Min (P25)",
        "Min (P50)",
        "Max (P50)",
        "Max (P75)",
    ]
    style_header(ws_salary, 4, salary_headers)

    benchmarks = metrics.get("salary_benchmarks") or []
    row_idx = 5
    for b in benchmarks:
        ws_salary.cell(row=row_idx, column=1, value=b.get("role", "")).font = cell_font
        ws_salary.cell(
            row=row_idx, column=2, value=b.get("currency", "")
        ).font = cell_font
        ws_salary.cell(
            row=row_idx, column=3, value=b.get("period", "")
        ).font = cell_font
        ws_salary.cell(
            row=row_idx, column=4, value=b.get("sample_size", 0)
        ).font = cell_font
        ws_salary.cell(
            row=row_idx, column=5, value=b.get("min_p25") or "N/A"
        ).font = cell_font
        ws_salary.cell(
            row=row_idx, column=6, value=b.get("min_p50") or "N/A"
        ).font = cell_font
        ws_salary.cell(
            row=row_idx, column=7, value=b.get("max_p50") or "N/A"
        ).font = cell_font
        ws_salary.cell(
            row=row_idx, column=8, value=b.get("max_p75") or "N/A"
        ).font = cell_font
        for c in range(1, 9):
            ws_salary.cell(row=row_idx, column=c).border = cell_border
        row_idx += 1

    # 3. Skills Gap Sheet
    ws_skills = wb.create_sheet("Skills Gap")
    ws_skills.cell(row=1, column=1, value="Skills Gap Analysis").font = title_font
    ws_skills.cell(
        row=2,
        column=1,
        value="Skills frequently required in jobs that are absent from candidate canonical profile",
    ).font = subtitle_font

    skills_headers = [
        "Skill",
        "Demand Frequency",
        "Market Percentage",
        "Priority Target",
    ]
    style_header(ws_skills, 4, skills_headers)

    skills_data = (metrics.get("skills_gap_analysis") or {}).get("skills", [])
    row_idx = 5
    for s in skills_data:
        ws_skills.cell(row=row_idx, column=1, value=s.get("skill", "")).font = cell_font
        ws_skills.cell(
            row=row_idx, column=2, value=s.get("frequency", 0)
        ).font = cell_font
        ws_skills.cell(
            row=row_idx, column=3, value=f"{s.get('percentage', 0)}%"
        ).font = cell_font
        ws_skills.cell(
            row=row_idx,
            column=4,
            value="HIGH PRIORITY" if s.get("priority") else "Secondary",
        ).font = cell_font
        for c in range(1, 5):
            ws_skills.cell(row=row_idx, column=c).border = cell_border
        row_idx += 1

    # 4. Stall Insights Sheet
    ws_stall = wb.create_sheet("Stall Insights")
    ws_stall.cell(
        row=1, column=1, value="Application Stall & Stage Funnel"
    ).font = title_font
    ws_stall.cell(
        row=2,
        column=1,
        value="Derived strictly from status transitions in ApplicationEvent (min 3 observations for median duration)",
    ).font = subtitle_font

    stall_headers = [
        "Stage",
        "Entered Count",
        "Progressed Count",
        "Dropped Count",
        "Drop-off Rate",
        "Median Dwell Time (Hours)",
        "Duration Sample Size",
    ]
    style_header(ws_stall, 4, stall_headers)

    stall_stages = (metrics.get("stall_insights") or {}).get("stages", [])
    row_idx = 5
    for st in stall_stages:
        rate = st.get("drop_off_rate")
        rate_str = f"{round(rate * 100, 1)}%" if rate is not None else "N/A"
        med = st.get("median_duration_hours")
        med_str = f"{med} hrs" if med is not None else "N/A"

        ws_stall.cell(
            row=row_idx, column=1, value=st.get("stage", "").title()
        ).font = cell_font
        ws_stall.cell(
            row=row_idx, column=2, value=st.get("entered_count", 0)
        ).font = cell_font
        ws_stall.cell(
            row=row_idx, column=3, value=st.get("progressed_count", 0)
        ).font = cell_font
        ws_stall.cell(
            row=row_idx, column=4, value=st.get("dropped_count", 0)
        ).font = cell_font
        ws_stall.cell(row=row_idx, column=5, value=rate_str).font = cell_font
        ws_stall.cell(row=row_idx, column=6, value=med_str).font = cell_font
        ws_stall.cell(
            row=row_idx, column=7, value=st.get("duration_sample_size", 0)
        ).font = cell_font
        for c in range(1, 8):
            ws_stall.cell(row=row_idx, column=c).border = cell_border
        row_idx += 1

    # 5. Conversion Funnel Sheet
    ws_funnel = wb.create_sheet("Conversion Funnel")
    ws_funnel.cell(row=1, column=1, value="Linear Conversion Funnel").font = title_font
    style_header(ws_funnel, 3, ["Stage", "Count"])
    row_idx = 4
    for item in metrics.get("conversion_funnel", []):
        ws_funnel.cell(
            row=row_idx, column=1, value=item.get("stage", "")
        ).font = cell_font
        ws_funnel.cell(
            row=row_idx, column=2, value=item.get("count", 0)
        ).font = cell_font
        ws_funnel.cell(row=row_idx, column=1).border = cell_border
        ws_funnel.cell(row=row_idx, column=2).border = cell_border
        row_idx += 1

    # Auto-adjust column widths across all sheets
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def create_analytics_snapshot(db: Session, user_id: uuid.UUID) -> AnalyticsSnapshot:
    """
    Create a new analytics snapshot for the user with schema_version=2.
    """
    metrics = generate_analytics_metrics(db, user_id)

    snapshot = AnalyticsSnapshot(
        user_id=user_id,
        snapshot_date=_utcnow(),
        metrics=metrics,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_latest_snapshot(db: Session, user_id: uuid.UUID) -> AnalyticsSnapshot | None:
    """
    Get the most recent analytics snapshot for a user.
    """
    return (
        db.query(AnalyticsSnapshot)
        .filter(AnalyticsSnapshot.user_id == user_id)
        .order_by(AnalyticsSnapshot.snapshot_date.desc())
        .first()
    )


def get_snapshots(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 20):
    """
    Get paginated analytics snapshots for a user.
    """
    query = db.query(AnalyticsSnapshot).filter(AnalyticsSnapshot.user_id == user_id)
    total = query.count()
    snapshots = (
        query.order_by(AnalyticsSnapshot.snapshot_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return snapshots, total
