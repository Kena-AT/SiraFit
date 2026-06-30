# Gemini API Integration Status

**Date**: June 30, 2026  
**Status**: ❌ NOT CONFIGURED

---

## Summary

**Gemini API integration is NOT currently implemented.** References to Gemini in the codebase are only in frontend UI placeholders and marketing copy. There is no actual backend integration.

---

## Current State

### Frontend UI (Placeholder Only)
The frontend has several **non-functional** Gemini UI elements:

1. **Settings Page** (`frontend/src/routes/_app.settings.ai.tsx`)
   - Shows Gemini API key input (placeholder)
   - Shows model selection (Gemini 1.5 Pro, Gemini 1.5 Flash)
   - "Test connection" button (not functional)
   - **Note**: This is just UI, no actual API integration

2. **Shell Component** (`frontend/src/components/sirafit/shell.tsx`)
   - Shows "Gemini · connected" badge
   - **Note**: This is hardcoded, not reflecting actual status

3. **Marketing Copy**
   - Landing page mentions "with your own Gemini key"
   - Privacy page says "Gemini API key stored locally only"
   - Help page mentions "Connect your Gemini key"
   - **Note**: These are aspirational features, not implemented

### Backend (No Integration)
❌ No Gemini API integration found in backend:
- No `google-generativeai` library in `requirements.txt`
- No API key configuration in `.env`
- No AI service module
- No Gemini client initialization
- No API calls to Gemini

### Current Scoring Logic
The `backend/app/services/scoring.py` file uses a **simple rule-based algorithm**:
- Keyword matching (50 points max)
- Experience title matching (30 points max)
- Profile completeness (20 points max)
- **No AI/ML involved**

---

## What's Missing

To implement Gemini API integration, you would need:

### 1. Backend Dependencies
```txt
# Add to requirements.txt
google-generativeai>=0.3.0
python-dotenv>=1.0.0  # Already installed
```

### 2. Environment Configuration
```env
# Add to .env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-pro  # or gemini-1.5-flash
```

### 3. Backend Service
Create `backend/app/services/ai_service.py`:
```python
import google.generativeai as genai
from app.core.config import settings

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

def analyze_job_match(profile_data: dict, job_data: dict) -> dict:
    """Use Gemini to analyze job-profile match"""
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    prompt = f"""
    Analyze this job match:
    
    Profile: {profile_data}
    Job: {job_data}
    
    Provide:
    1. Match score (0-100)
    2. Key strengths
    3. Skill gaps
    4. Recommendations
    """
    
    response = model.generate_content(prompt)
    return parse_response(response.text)
```

### 4. API Endpoints
Add to `backend/app/api/` endpoints:
- `POST /api/v1/ai/analyze-match` - Analyze job-profile match
- `POST /api/v1/ai/generate-resume` - Generate tailored resume
- `POST /api/v1/ai/generate-cover-letter` - Generate cover letter
- `GET /api/v1/ai/status` - Check AI service status

### 5. Frontend Integration
Update `frontend/src/lib/api/ai.ts`:
```typescript
export const analyzeMatch = async (profileId: string, jobId: string) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai/analyze-match`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ profileId, jobId }),
  });
  return response.json();
};
```

### 6. Settings Page Implementation
Make the AI settings page functional:
- Store API key in user preferences (encrypted)
- Test connection button actually tests the key
- Model selection changes which Gemini model to use
- Display usage statistics

---

## Recommended Implementation Plan

### Phase 1: Basic Integration (Sprint 4)
1. Add `google-generativeai` to requirements
2. Add `GEMINI_API_KEY` to .env
3. Create `ai_service.py` with basic Gemini client
4. Add health check endpoint to verify API key works
5. Update settings page to save/test API key

### Phase 2: Job Matching Enhancement (Sprint 4)
1. Replace rule-based scoring with AI analysis
2. Generate detailed match explanations
3. Identify skill gaps and strengths
4. Provide application recommendations

### Phase 3: Resume Generation (Sprint 6)
1. Generate tailored resumes per job
2. Optimize content for ATS systems
3. Suggest improvements
4. Export to PDF/DOCX

### Phase 4: Cover Letters (Sprint 6)
1. Generate personalized cover letters
2. Match tone to company culture
3. Highlight relevant experience
4. Multiple style options

---

## Security Considerations

### API Key Storage
**Option 1: User-Provided (Current UI Design)**
- Pros: Users control their own costs
- Pros: No SiraFit liability for API usage
- Cons: More friction for users
- Cons: Need to store keys securely per user

**Option 2: SiraFit-Provided**
- Pros: Simpler user experience
- Pros: Centralized cost management
- Cons: Higher operational costs
- Cons: Need usage quotas per user

### Recommended: User-Provided (as designed)
The current UI design expects users to bring their own Gemini API key:
- Store encrypted in database (User preferences)
- Never log or expose in responses
- Allow users to update/delete anytime
- Test connection before saving

### Implementation
```python
# backend/app/models/user.py
class UserPreference(Base):
    # ... existing fields ...
    gemini_api_key_encrypted = Column(Text, nullable=True)
    gemini_model = Column(String(50), default="gemini-1.5-pro")
    
# Encrypt/decrypt methods
from cryptography.fernet import Fernet

def encrypt_api_key(key: str) -> str:
    f = Fernet(settings.ENCRYPTION_KEY)
    return f.encrypt(key.encode()).decode()

def decrypt_api_key(encrypted: str) -> str:
    f = Fernet(settings.ENCRYPTION_KEY)
    return f.decrypt(encrypted.encode()).decode()
```

---

## Cost Estimation

### Gemini API Pricing (as of 2024)
**Gemini 1.5 Pro**:
- Input: $3.50 per 1M tokens
- Output: $10.50 per 1M tokens

**Gemini 1.5 Flash**:
- Input: $0.35 per 1M tokens  
- Output: $1.05 per 1M tokens

### Estimated Usage per Feature
**Job Match Analysis**: ~500 tokens input + ~300 tokens output
- Pro: $0.0049 per analysis
- Flash: $0.00049 per analysis

**Resume Generation**: ~2000 tokens input + ~1500 tokens output
- Pro: $0.0228 per resume
- Flash: $0.00228 per resume

**Cover Letter**: ~1500 tokens input + ~800 tokens output
- Pro: $0.0136 per letter
- Flash: $0.00136 per letter

### Monthly Cost Estimate (per user)
- 50 job analyses + 10 resumes + 10 cover letters
- **Gemini Pro**: ~$0.70/month/user
- **Gemini Flash**: ~$0.07/month/user

**Recommendation**: Use Gemini Flash for most operations, Pro for complex resume generation.

---

## Testing Without Implementation

Since Gemini is not implemented, the following features will NOT work:
- ❌ AI-powered job matching
- ❌ Detailed match explanations beyond keyword matching
- ❌ Resume generation
- ❌ Cover letter generation
- ❌ Skill gap analysis with AI insights
- ❌ Application recommendations

What DOES work:
- ✅ Basic rule-based scoring (keyword matching)
- ✅ Manual resume editing (Sprint 2)
- ✅ Job import (Sprint 3)
- ✅ All CRUD operations

---

## Quick Setup Guide (For Future Implementation)

### 1. Get Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)

### 2. Install Python Library
```bash
cd backend
pip install google-generativeai
pip freeze > requirements.txt
```

### 3. Add to .env
```env
GEMINI_API_KEY=AIzaSy...your_key_here
GEMINI_MODEL=gemini-1.5-flash
```

### 4. Test Connection
```python
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("Say hello!")
print(response.text)
```

### 5. Update Settings
Add to `backend/app/core/config.py`:
```python
class Settings(BaseSettings):
    # ... existing settings ...
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
```

---

## Conclusion

**Current Status**: ❌ Gemini API is NOT configured

**What Exists**: 
- Frontend UI placeholders
- Marketing copy mentioning Gemini
- Non-functional "connected" badge

**What's Missing**:
- Backend integration
- API key configuration
- AI service module
- Functional endpoints
- Actual API calls

**Next Steps**:
1. Decide if you want to implement Gemini integration
2. Choose between user-provided vs SiraFit-provided API keys
3. Follow the implementation plan above
4. Start with Phase 1 (basic integration) in Sprint 4

**Estimated Implementation Time**: 2-3 days for basic integration

---

**Status**: Not Configured ❌  
**Priority**: Medium (Nice to have, not required for Sprint 3)  
**Blocker**: No (current features work without it)
