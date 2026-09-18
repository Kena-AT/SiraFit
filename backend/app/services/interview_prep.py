import uuid
import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field

from app.models.profile import Profile
from app.models.job import Job
from app.models.ai_completion import AICompletion
from app.services.ai_keys import build_candidates
from app.services.structured_ai import structured_completion_with_fallback
from app.services.gap_to_plan import generate_learning_plan


class InterviewQuestion(BaseModel):
    question: str = Field(..., description="The interview question text.")
    focus_skill: str = Field(
        ...,
        description="The skill this question aims to evaluate, typically one the candidate is missing.",
    )
    ideal_answer_points: List[str] = Field(
        ..., description="Bullet points of what a good answer should include."
    )


class InterviewQuestions(BaseModel):
    questions: List[InterviewQuestion] = Field(
        ...,
        description="List of 3 specific interview questions.",
        min_length=3,
        max_length=3,
    )


RATE_LIMIT_24H = 10


class RateLimitExceeded(Exception):
    pass


async def generate_prep_questions(
    db: Session, user_id: uuid.UUID, profile: Profile, job: Job
) -> Dict[str, Any]:
    """
    Generates 3 specific interview questions based on the candidate's skill gaps to the job.
    Enforces a strict rate limit of 10 generations per user per 24 hours.
    """
    # 1. Check Rate Limits (using AICompletion table)
    yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=1
    )

    usage_count = (
        db.query(func.count(AICompletion.id))
        .filter(
            AICompletion.user_id == user_id,
            AICompletion.operation == "interview_prep",
            AICompletion.created_at >= yesterday,
        )
        .scalar()
        or 0
    )

    if usage_count >= RATE_LIMIT_24H:
        raise RateLimitExceeded(
            f"Rate limit exceeded: You can only generate {RATE_LIMIT_24H} interview preps per 24 hours."
        )

    # 2. Determine skill gaps to guide the LLM
    gap_plan = generate_learning_plan(db, profile, job)
    missing_skills = gap_plan["missing_skills"]

    missing_skills_text = ", ".join(missing_skills) if missing_skills else "None"
    profile_skills_text = (
        ", ".join([s.name for s in profile.skills]) if profile.skills else "None"
    )

    # 3. Prepare AI Request
    system_prompt = (
        "You are an expert technical interviewer. Based on a candidate's profile and the job they are applying for, "
        "generate exactly 3 highly specific interview questions. Focus heavily on evaluating their capability to learn or "
        "compensate for their missing skills, or assessing their core strengths against the job requirements."
    )

    user_prompt = (
        f"Job Title: {job.title}\n"
        f"Job Description snippet: {job.description[:1000]}\n\n"
        f"Candidate's Current Skills: {profile_skills_text}\n"
        f"Candidate's Missing Skills for this Job: {missing_skills_text}\n\n"
        "Please generate 3 specific interview questions and the ideal answer points for each."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    candidates = build_candidates(db=db, user_id=user_id)

    if not candidates:
        raise RuntimeError(
            "No AI candidates configured. Please configure an AI provider in Settings."
        )

    # 4. Generate structured output
    result_model, ai_completion = await structured_completion_with_fallback(
        operation="interview_prep",
        response_model=InterviewQuestions,
        messages=messages,
        candidates=candidates,
        db=db,
        user_id=user_id,
        temperature=0.7,
    )

    return {
        "questions": [q.model_dump() for q in result_model.questions],
        "usage_count": usage_count + 1,
        "rate_limit": RATE_LIMIT_24H,
    }
