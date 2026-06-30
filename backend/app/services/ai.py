import json
import httpx
import logging
from typing import Tuple, Dict, Any
import google.generativeai as genai
from app.models.profile import Profile
from app.models.job import Job

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """
You are an expert technical recruiter and resume screener. 
Please analyze the following candidate profile against the job description and provide a match score (0-100) and a brief reason.
Output MUST be valid JSON in this exact format, with no markdown formatting or extra text:
{"score": 85, "reason": "Candidate has strong React experience but lacks Python."}
"""

def serialize_profile(profile: Profile) -> str:
    if not profile:
        return "{}"
    return json.dumps({
        "headline": profile.headline,
        "summary": profile.summary,
        "skills": [s.name for s in getattr(profile, "skills", [])] if profile.skills else [],
        "experiences": [
            {"title": e.title, "company": e.company, "description": e.description}
            for e in getattr(profile, "experiences", [])
        ] if profile.experiences else []
    })

def serialize_job(job: Job) -> str:
    if not job:
        return "{}"
    return json.dumps({
        "title": job.title,
        "company": job.company,
        "description": job.description,
        "requirements": getattr(job, "requirements", []),
        "tags": getattr(job, "tags", [])
    })

async def analyze_job_match_gemini(profile: Profile, job: Job, api_key: str, model: str) -> Tuple[int, str]:
    try:
        genai.configure(api_key=api_key)
        model_name = "models/gemini-1.5-pro" if "pro" in model.lower() else "models/gemini-1.5-flash"
        
        prompt = f"{ANALYSIS_PROMPT}\n\nCandidate Profile:\n{serialize_profile(profile)}\n\nJob Description:\n{serialize_job(job)}"
        
        gen_model = genai.GenerativeModel(model_name)
        response = gen_model.generate_content(prompt)
        
        return _parse_ai_response(response.text)
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return 0, f"Gemini API error: {str(e)}"

async def analyze_job_match_openrouter(profile: Profile, job: Job, api_key: str, model: str) -> Tuple[int, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://sirafit.com", 
        "Content-Type": "application/json"
    }
    
    prompt = f"{ANALYSIS_PROMPT}\n\nCandidate Profile:\n{serialize_profile(profile)}\n\nJob Description:\n{serialize_job(job)}"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
        response_text = data["choices"][0]["message"]["content"]
        return _parse_ai_response(response_text)
    except Exception as e:
        logger.error(f"OpenRouter API error: {e}")
        return 0, f"OpenRouter API error: {str(e)}"

def _parse_ai_response(text: str) -> Tuple[int, str]:
    try:
        clean_text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_text)
        return int(result.get("score", 0)), result.get("reason", "No reason provided.")
    except Exception as e:
        return 0, f"Failed to parse AI response: {str(e)}"
