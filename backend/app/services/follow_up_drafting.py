"""
AI-powered application follow-up drafting service.

Generates personalized, stage-aware follow-up messages and timeline notes
using the user's preferred AI model from Settings.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.job import JobApplication, Job
from app.models.profile import Profile
from app.services.ai_keys import build_candidates
from app.services.structured_ai import structured_completion_with_fallback

logger = logging.getLogger(__name__)


class FollowUpDraftOutput(BaseModel):
    subject: str = Field(..., description="Email subject line for the follow-up message.")
    body: str = Field(..., description="The complete follow-up email/message text.")
    draft_note: str = Field(
        ...,
        description="A concise summary action note suitable for the application's follow-up note field.",
    )


async def draft_stage_follow_up(
    db: Session,
    user_id: uuid.UUID,
    application: JobApplication,
    profile: Optional[Profile] = None,
) -> Dict[str, Any]:
    """
    Draft a stage-specific follow-up message for a job application.
    Prioritizes user's preferred model via build_candidates.
    """
    job: Optional[Job] = application.job
    job_title = job.title if job else "Role"
    company = job.company if job else "Company"
    status_stage = application.status or "applied"

    candidate_name = ""
    candidate_skills = ""
    if profile:
        first = profile.first_name or ""
        last = profile.last_name or ""
        candidate_name = f"{first} {last}".strip()
        if profile.skills:
            candidate_skills = ", ".join(s.name for s in profile.skills[:10])

    # Contact context if available
    contact_names = []
    if application.contacts:
        for c in application.contacts:
            contact_names.append(f"{c.name} ({c.role})")
    contacts_str = ", ".join(contact_names) if contact_names else "Hiring Team"

    # Stage specific guidance
    stage_guidance = {
        "applied": "1-2 weeks post-submission. Polite check-in confirming receipt, reiterating strong enthusiasm and 1 key matching qualification.",
        "screening": "Post-recruiter screen. Warm thank you referencing conversational rapport, re-emphasizing mutual excitement for the team.",
        "interview": "Post-technical or hiring manager interview. Targeted thank-you referencing specific challenges discussed and demonstrating problem-solving alignment.",
        "final_round": "Post-final round. Executive-level note reaffirming alignment with organizational goals and readiness to hit the ground running.",
        "offer": "Offer stage. Polite appreciation while evaluating terms or preparing negotiation points.",
    }.get(
        status_stage,
        "Polite, proactive follow-up inquiring about status and expressing continued interest.",
    )

    system_prompt = (
        "You are an executive career coach. Generate a concise, highly tailored follow-up "
        "communication for a job application. Maintain a professional, confident, and respectful tone. "
        "Do not invent false background information."
    )

    user_prompt = (
        f"Candidate: {candidate_name or 'Candidate'}\n"
        f"Key Skills: {candidate_skills or 'Engineering'}\n"
        f"Target Role: {job_title}\n"
        f"Company: {company}\n"
        f"Application Stage: {status_stage}\n"
        f"Known Contacts: {contacts_str}\n"
        f"Stage Guidance: {stage_guidance}\n\n"
        "Generate a tailored email subject, email body, and a short 1-sentence draft note for the follow-up reminder."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    candidates = build_candidates(db=db, user_id=user_id)
    if not candidates:
        # Fallback heuristic if no AI candidate configured
        return {
            "subject": f"Following up on application for {job_title} - {candidate_name or 'Candidate'}",
            "body": (
                f"Dear {company} Team,\n\n"
                f"I am following up on my application for the {job_title} position. "
                "I remain very interested in the role and would welcome an update on your timeline.\n\n"
                f"Best regards,\n{candidate_name or 'Candidate'}"
            ),
            "draft_note": f"Follow up with {company} regarding {job_title} status",
        }

    try:
        result_model, _ = await structured_completion_with_fallback(
            operation="follow_up_drafting",
            response_model=FollowUpDraftOutput,
            messages=messages,
            candidates=candidates,
            db=db,
            user_id=user_id,
            temperature=0.4,
        )
        return result_model.model_dump()
    except Exception as exc:
        logger.warning("AI follow-up drafting failed (%s); returning fallback draft", exc)
        return {
            "subject": f"Following up on {job_title} position at {company}",
            "body": (
                f"Dear {contacts_str},\n\n"
                f"I wanted to follow up on the status of my application for the {job_title} role at {company}. "
                "I remain enthusiastic about the opportunity to contribute to your team.\n\n"
                f"Best regards,\n{candidate_name or 'Candidate'}"
            ),
            "draft_note": f"Follow up with {contacts_str} on {status_stage} status",
        }


# Backward-compatible alias
draft_follow_up = draft_stage_follow_up
