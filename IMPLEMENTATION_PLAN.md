# SiraFit Implementation Plan: Fix All Identified Issues

## Overview

This document outlines a comprehensive implementation plan to address all identified issues in SiraFit, grouped by severity. The plan includes technical details, implementation steps, and dependencies.

---

## HIGH SEVERITY (Broken / Non-functional)

### 1. Password Change Endpoint

**Problem**: No PUT `/users/me/password` endpoint exists. The existing PUT `/users/me` strips the password field.

**Implementation Steps**:
- [ ] Create new endpoint in `backend/app/api/users.py` or `backend/app/core/auth.py`
- [ ] Add `PUT /users/me/password` route that:
  - Validates current password
  - Accepts new password with confirmation
  - Hashes new password with bcrypt/argon2
  - Updates user record
- [ ] Add Pydantic schema for password change request
- [ ] Update frontend settings page to call the new endpoint
- [ ] Remove mock setTimeout and 500ms delay

**Technical Details**:
```python
# backend/app/api/users.py
@router.put("/me/password", dependencies=[Depends(get_current_user)])
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Hash and update
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}
```

---

### 2. Data Export & Account Deletion Endpoints

**Problem**: No backend endpoints for export or deletion; frontend uses mocks.

**Implementation Steps**:

**Data Export**:
- [ ] Create `GET /users/me/export` endpoint
- [ ] Implement data serialization (JSON/CSV)
- [ ] Queue export generation (async for large datasets)
- [ ] Add download endpoint or file storage (S3/local)
- [ ] Update frontend to call real endpoint

**Account Deletion**:
- [ ] Create `DELETE /users/me` endpoint
- [ ] Implement soft-delete or hard-delete logic
- [ ] Clear user data from all tables
- [ ] Remove associated files (resumes, applications, etc.)
- [ ] Invalidate all sessions
- [ ] Return appropriate response
- [ ] Update frontend to call real endpoint

**Technical Details**:
```python
# backend/app/api/users.py
@router.get("/me/export", dependencies=[Depends(get_current_user)])
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Gather all user data
    user_data = {
        "profile": user_profile_schema,
        "applications": [...],
        "jobs": [...],
        # etc.
    }
    return JSONResponse(content=user_data)

@router.delete("/me", dependencies=[Depends(get_current_user)])
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Cascade delete all related records
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}
```

---

### 3. notification_service.py Import Error

**Problem**: `from app.services.email import send_email` fails because `email.py` exports `EmailService` class and instance, not a function.

**Implementation Steps**:
- [ ] Option A: Add `send_email` function to `email.py`:
  ```python
  def send_email(to: str, subject: str, body: str):
      return email_service.send(to, subject, body)
  ```
- [ ] Option B: Update `notification_service.py` to use `email_service` instance:
  ```python
  from app.services.email import email_service
  # Use email_service.send(...) instead
  ```
- [ ] Fix Celery task imports
- [ ] Test notification workers

**Technical Details**:
The `notification_service.py` should be refactored to:
```python
from app.services.email import email_service

def send_notification(user_id: int, message: str):
    # Get user email
    # Send via email_service.send(to, subject, body)
    pass
```

---

### 4. GET /jobs/ranked Route Order

**Problem**: Route order causes `/jobs/ranked` to match `{job_id}` pattern first.

**Implementation Steps**:
- [ ] Move `GET /jobs/ranked` route definition BEFORE `GET /jobs/{job_id}` in `router.py`
- [ ] Verify route order in FastAPI registration
- [ ] Test that `/jobs/ranked` returns correctly

**Technical Details**:
In FastAPI, routes are matched in the order they're registered. The fix is simple:
```python
# backend/app/api/router.py
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
# Ensure ranked route is defined BEFORE {job_id} in jobs router
```

---

## MEDIUM SEVERITY (Silently broken or incomplete)

### 5. Notification Preferences

**Problem**: Mutation is mocked; no backend endpoints exist.

**Implementation Steps**:
- [ ] Create `UserPreference` model fields for notification settings
- [ ] Create `GET /users/me/preferences/notifications` endpoint
- [ ] Create `PUT /users/me/preferences/notifications` endpoint
- [ ] Add Pydantic schemas for notification preferences
- [ ] Update frontend to call real endpoints

**Schema**:
```python
class NotificationPreferences(BaseModel):
    email_job_matches: bool = True
    email_daily_summary: bool = False
    push_notifications: bool = True
    email_new_opportunities: bool = True
```

---

### 6. Resume Defaults

**Problem**: Template, auto-tailor, export format are local state only.

**Implementation Steps**:
- [ ] Add fields to `UserPreference` model:
  - `default_template: str`
  - `auto_tailor_enabled: bool`
  - `export_format: str`
- [ ] Create `GET /users/me/preferences/resume` endpoint
- [ ] Create `PUT /users/me/preferences/resume` endpoint
- [ ] Update frontend to persist preferences

---

### 7. Analytics Missing Fields

**Problem**: `top_technologies`, `salary_medians`, `skill_gaps` not returned by backend.

**Implementation Steps**:
- [ ] Update `generate_analytics_metrics()` in `backend/app/services/analytics.py`
- [ ] Add `top_technologies` calculation:
  - Query most common skills in recent applications
  - Return as list of [skill_name, count] pairs
- [ ] Add `salary_medians` calculation:
  - Query salary data from jobs
  - Group by sector/role
  - Calculate median
- [ ] Add `skill_gaps` analysis:
  - Compare user skills vs job requirements
  - Return gaps with impact scores
- [ ] Remove hardcoded fake data from frontend

---

### 8. Analytics Rejection Stages

**Problem**: All stages query same status, no stage distinction.

**Implementation Steps**:
- [ ] Update `JobApplication` model to track rejection stage:
  ```python
  class JobApplication(Base):
      __tablename__ = "job_applications"
      # existing fields...
      rejection_stage = Column(String, nullable=True)  # "resume_screen", "recruiter_call", "tech_screen", "onsite"
  ```
- [ ] Update rejection stage queries to filter by `rejection_stage`
- [ ] Update frontend to display correct counts per stage

---

### 9. UserPreference AI Provider Keys

**Problem**: 5 AI provider key fields missing from DB model.

**Implementation Steps**:
- [ ] Add missing columns to `UserPreference` model:
  - `encrypted_anthropic_key`
  - `encrypted_openai_key`
  - `encrypted_grok_key`
  - `encrypted_mistral_key`
  - `encrypted_nvidia_key`
- [ ] Run database migration (Alembic)
- [ ] Update `job_analysis.py` and `scoring.py` to use DB keys
- [ ] Remove `hasattr()` guards

---

## LOW SEVERITY (Stubs / Placeholders)

### 10. Top Match Queue Empty

**Problem**: `_get_top_match_queue()` returns empty list.

**Implementation Steps**:
- [ ] Implement match scoring algorithm
- [ ] Query user profile and job data
- [ ] Calculate match scores
- [ ] Return top 4 matches with scores

**Algorithm Outline**:
```python
def _get_top_match_queue(db: Session, user_id: int) -> List[TopMatchItem]:
    # Get user profile skills
    user_skills = get_user_skills(user_id)
    
    # Get unsaved jobs
    jobs = get_unsaved_jobs(user_id)
    
    # Calculate matches
    matches = []
    for job in jobs:
        score = calculate_match_score(user_skills, job)
        matches.append({
            "company": job.company,
            "role": job.title,
            "match_score": score,
            "status": "new"
        })
    
    # Sort and return top 4
    return sorted(matches, key=lambda x: x["match_score"], reverse=True)[:4]
```

---

### 11. notification.py Router Orphaned

**Problem**: Router file exists but is never registered.

**Implementation Steps**:
- [ ] Register router in `backend/app/api/router.py`:
  ```python
  from app.api import notification
  api_router.include_router(notification.router, prefix="/notifications", tags=["notifications"])
  ```
- [ ] Verify all routes are accessible

---

### 12. Market Trend Always "+0%"

**Problem**: Change field is hardcoded.

**Implementation Steps**:
- [ ] Store historical data for market trends
- [ ] Calculate percentage change from previous period
- [ ] Return actual percentage

**Implementation**:
```python
# Store historical metrics in database
# Calculate: (current - previous) / previous * 100
```

---

### 13. Import History Detail Empty

**Problem**: Always returns empty jobs and errors.

**Implementation Steps**:
- [ ] Update `GET /jobs/import/{import_id}` to query actual jobs
- [ ] Filter jobs by import batch ID
- [ ] Return errors if any occurred during import

---

### 14. Devices Panel Fake Data

**Problem**: Hardcoded MacBook Pro entry.

**Implementation Steps**:
- [ ] Create `DeviceSession` model
- [ ] Track sessions with device info, IP, user agent
- [ ] Create `GET /users/me/devices` endpoint
- [ ] Update frontend to display real data

**Model**:
```python
class DeviceSession(Base):
    __tablename__ = "device_sessions"
    id: int
    user_id: int
    device_name: str
    ip_address: str
    user_agent: str
    is_active: bool
    last_seen: datetime
```

---

### 15. Help Page Dead Links

**Problem**: Article cards have no href.

**Implementation Steps**:
- [ ] Create documentation pages or external links
- [ ] Add `href` to each article card
- [ ] Or implement internal documentation system

---

## Implementation Priority Order

1. **High Severity First**:
   - Password change endpoint
   - Data export & deletion
   - notification_service.py import
   - /jobs/ranked route order

2. **Medium Severity**:
   - Notification preferences
   - Resume defaults persistence
   - Analytics missing fields
   - Rejection stages tracking
   - AI provider keys in DB

3. **Low Severity**:
   - Top match queue implementation
   - Register notification router
   - Market trend calculation
   - Import history detail
   - Devices panel
   - Help page links

---

## Database Migrations Required

| Migration | Description |
|-----------|-------------|
| 001_add_rejection_stage | Add rejection_stage to job_applications |
| 002_add_ai_provider_keys | Add encrypted key columns to user_preferences |
| 003_add_notification_prefs | Add notification preference fields |
| 004_add_resume_defaults | Add resume default fields |
| 005_add_device_sessions | Add device_sessions table |
| 006_add_market_history | Add historical market data table |

---

## Testing Requirements

For each feature, implement:
- Unit tests for backend endpoints
- Integration tests for full flow
- Frontend tests for UI interactions
- E2E tests for critical user journeys

---

## Estimated Effort

| Severity | Issues | Estimated Hours |
|----------|--------|-----------------|
| High | 4 | 24-32 |
| Medium | 5 | 40-56 |
| Low | 6 | 32-48 |
| **Total** | **15** | **96-136 hours** |

---

## Dependencies

- Database migrations must run before backend features
- API endpoints must exist before frontend implementation
- User preference fields must be added before analytics improvements