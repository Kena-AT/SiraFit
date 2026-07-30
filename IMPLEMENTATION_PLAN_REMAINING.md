# SiraFit Implementation Plan: Remaining 10 Issues

Overview of remaining unimplemented features grouped by area and priority.

---

## NOTIFICATION PREFERENCES ENDPOINTS (Medium)

### Issue
Mutation is mocked; no backend endpoints exist for notification preferences.

### Implementation
- [ ] Add notification preference fields to `UserPreference` DB model (email_job_matches, email_daily_summary, push_notifications, email_new_opportunities)
- [ ] Create `GET /users/me/preferences/notifications` endpoint
- [ ] Create `PUT /users/me/preferences/notifications` endpoint
- [ ] Update Pydantic schema (`NotificationPreferences`) in `schemas/user.py`
- [ ] Wire frontend settings page to call real endpoints (remove mock setTimeout)

---

## RESUME DEFAULTS PERSISTENCE (Medium)

### Issue
Template, auto-tailor, and export format are local state only; no DB persistence.

### Implementation
- [ ] Add fields to `UserPreference` model: `default_template` (str), `auto_tailor_enabled` (bool), `export_format` (str)
- [ ] Create `GET /users/me/preferences/resume` endpoint
- [ ] Create `PUT /users/me/preferences/resume` endpoint
- [ ] Update frontend resume settings to persist via API
- [ ] Run Alembic migration for new columns

---

## ANALYTICS MISSING FIELDS (Medium)

### Issue
`top_technologies`, `salary_medians`, `skill_gaps` not returned by `/analytics` endpoint.

### Implementation
- [ ] In `backend/app/services/analytics.py`, update `generate_analytics_metrics()`:
  - `top_technologies`: query most frequent skills from user applications, return `[{"skill": str, "count": int}]`
  - `salary_medians`: group jobs by sector/role, calculate median salary, return `{sector: float}`
  - `skill_gaps`: compare user skills against target job requirements, return gaps with impact scores
- [ ] Remove hardcoded placeholder arrays from frontend analytics component
- [ ] Add response schema fields for the three metrics

---

## ANALYTICS REJECTION STAGES TRACKING (Medium)

### Issue
All rejection stages query the same `rejected` status; no stage-level distinction.

### Implementation
- [ ] Add `rejection_stage` (String, nullable) to `JobApplication` model: values: `resume_screen`, `recruiter_call`, `tech_screen`, `onsite`
- [ ] Update `analytics.py` stage queries to filter by `rejection_stage = <stage>`
- [ ] Update frontend funnel chart to display accurate per-stage counts
- [ ] Run Alembic migration: `add_rejection_stage_to_job_applications`

---

## USERPREFERENCE AI PROVIDER KEYS (Medium)

### Issue
5 AI provider key fields missing from DB model; `job_analysis.py` and `scoring.py` rely on `hasattr()` guards.

### Implementation
- [ ] Add encrypted columns to `UserPreference`: `encrypted_anthropic_key`, `encrypted_openai_key`, `encrypted_grok_key`, `encrypted_mistral_key`, `encrypted_nvidia_key` (String, nullable)
- [ ] Run Alembic migration: `add_ai_provider_keys_to_user_preferences`
- [ ] Update `backend/app/services/job_analysis.py` and `scoring.py` to read keys from DB instead of using `hasattr()` fallbacks
- [ ] Update settings page to save/load keys through `PUT /users/me/preferences/ai-keys`

---

## TOP MATCH QUEUE IMPLEMENTATION (Low)

### Issue
`_get_top_match_queue()` returns empty list always.

### Implementation
- [ ] Implement match scoring: query active/unmatched jobs, calculate score from user skills vs job requirements, return top 4 sorted by score
- [ ] Add `TopMatchItem` response schema with fields: `company`, `role`, `match_score`, `status` (`new` / `saved`)
- [ ] Update dashboard component to display real queue items instead of mock data

---

## MARKET TREND CALCULATION (Low)

### Issue
Market trend always shows `+0%`; no historical comparison.

### Implementation
- [ ] Create historical market metrics storage (table or cache) to record prior period values
- [ ] Update `analytics.py` market trend endpoint to compute `(current - previous) / previous * 100`
- [ ] Return actual percentage string (e.g., `+12.3%` or `-4.1%`) instead of hardcoded `+0%`
- [ ] Add `trend` field to analytics response schema

---

## IMPORT HISTORY DETAIL (Low)

### Issue
`GET /jobs/import/{import_id}` always returns empty `jobs` and `errors`.

### Implementation
- [ ] Query `JobApplication` table by `import_batch_id` or `import_id` to return actual imported jobs
- [ ] Return `errors` array from import log if any parsing errors occurred
- [ ] Update frontend import history detail component to render real data

---

## DEVICES PANEL (Low)

### Issue
Devices panel shows hardcoded `MacBook Pro` entry; no real session tracking.

### Implementation
- [ ] Create `DeviceSession` DB model: `id`, `user_id`, `device_name`, `ip_address`, `user_agent`, `is_active`, `last_seen`
- [ ] Create `GET /users/me/devices` endpoint returning active/inactive sessions
- [ ] Create `DELETE /users/me/devices/{device_id}` endpoint for revoking sessions
- [ ] Replace hardcoded card data in frontend `Devices` component

---

## HELP PAGE LINKS (Low)

### Issue
Article cards have no `href`; links are dead.

### Implementation
- [ ] Add `href` field to help article data structure in frontend
- [ ] Link cards to external documentation URLs or create internal doc pages (`/docs/getting-started`, `/docs/profile-setup`)
- [ ] Ensure all cards navigate correctly (external links open in new tab)

---

## Implementation Order

1. **Medium (DB + API)**: Notification Preferences → Resume Defaults → AI Provider Keys (needs migrations first)
2. **Medium (Analytics)**: Analytics Missing Fields → Rejection Stages → Market Trend
3. **Low (UI + Tracking)**: Top Match Queue → Import History → Devices Panel → Help Links

## Dependencies Between Items
- AI Provider Keys and Notification Preferences both need `UserPreference` migrations; run migrations together before implementing features
- Analytics fields depend on correct DB data; fix DB first, then analytics
- Devices Panel requires new `DeviceSession` table; migration before endpoint

## Migration List (Remaining)

| # | Migration Name | Affected Tables |
|---|---------------|-----------------|
| 1 | `add_notification_prefs` | `user_preferences` |
| 2 | `add_resume_defaults` | `user_preferences` |
| 3 | `add_ai_provider_keys` | `user_preferences` |
| 4 | `add_rejection_stage` | `job_applications` |
| 5 | `add_device_sessions` | `device_sessions` (new) |
| 6 | `add_import_batch_id` | `job_applications` |
| 7 | `add_market_history` | `market_trend_history` (new) |