import os
import json
import google.generativeai as genai
from typing import Dict, Any

# Configure Gemini
# Note: Ensure GEMINI_API_KEY is set in your environment
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_job(job: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"""
    Analyze the following job description and provide structured insights.
    Return ONLY valid JSON. Do not include any other text or formatting.
    
    Job Title: {job['title']}
    Company: {job['company']}
    Description: {job.get('description', 'No description provided')}
    
    Required JSON format:
    {{
      "score": 85,
      "summary": "Brief summary of the role...",
      "pros": ["Pro 1", "Pro 2"],
      "cons": ["Con 1", "Con 2"],
      "skills_gap": ["Skill 1", "Skill 2"]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean response for JSON parsing
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        # Fallback in case of AI parsing failure
        return {
            "score": 0,
            "summary": "Analysis failed",
            "pros": [],
            "cons": [],
            "skills_gap": []
        }
