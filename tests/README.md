# Test Suite Directory

This directory contains comprehensive end-to-end and integration tests for the SiraFit application.

## Structure

```
tests/
├── complete-user-journey.spec.ts     # Frontend E2E tests (Playwright) - MAIN test
├── test_complete_user_journey.py     # Backend integration tests (pytest) - MAIN test
├── conftest.py                       # Pytest fixtures
├── test_auth.py                      # Backend auth tests
├── test_application_tracking.py      # Application tracking tests
├── test_notifications.py             # Notifications service tests
├── test_job_import.py                # Job import tests
├── test_profiles.py                  # Profile tests
├── test_resume_generation.py         # Resume generation tests
├── test_resume_export.py             # Resume export tests
├── test_batch_operations.py          # Batch operations tests
├── test_batch_api.py                 # Batch API tests
├── test_analytics.py                 # Analytics tests
├── test_job_search.py                # Job search tests
├── test_pdf_rendering.py             # PDF rendering tests
├── test_worker_tasks.py              # Worker tasks tests
├── test_cover_letter_generation.py   # Cover letter tests
├── test_job_analysis.py              # Job analysis tests
├── test_job_match_score.py           # Job match score tests
├── test_email.py                     # Email tests
├── job-explorer.spec.ts              # Job explorer E2E tests
├── job-import.spec.ts                # Job import E2E tests
├── profile-editor.spec.ts            # Profile editor E2E tests
├── route-protection.spec.ts          # Route protection E2E tests
└── README.md                         # This file
```

## Running Tests

### Backend Integration Tests (pytest)

```bash
cd backend

# Install dev dependencies
rtk pip install -r requirements-dev.txt

# Run MAIN complete journey tests
rtk pytest ../tests/test_complete_user_journey.py -v

# Run specific test class
rtk pytest ../tests/test_complete_user_journey.py::TestCompleteUserJourney -v

# Run specific test
rtk pytest ../tests/test_complete_user_journey.py::TestCompleteUserJourney::test_20_full_application_workflow -v

# Run with coverage
rtk pytest ../tests/test_complete_user_journey.py --cov=app --cov-report=term-missing

# Run all backend tests
rtk pytest ../tests/ -v
```

### Frontend E2E Tests (Playwright)

```bash
cd frontend

# Install dependencies (includes Playwright)
rtk pnpm install

# Install Playwright browsers
rtk npx playwright install

# Start backend server (Terminal 1)
cd backend && rtk python -m uvicorn app.main:app --reload --port 8000

# Start frontend server (Terminal 2)
cd frontend && rtk pnpm dev

# Run MAIN E2E tests (Terminal 3)
cd tests && rtk npx playwright test complete-user-journey.spec.ts --headed

# Run with HTML report
rtk npx playwright test complete-user-journey.spec.ts --reporter=html
rtk npx playwright show-report

# Run all E2E tests
rtk npx playwright test --headed
```

### Combined Test Run

1. Start backend: `cd backend && rtk python -m uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && rtk pnpm dev`
3. Run E2E: `cd tests && rtk npx playwright test complete-user-journey.spec.ts`

## Test Coverage

The **main tests** cover the complete user journey:

### `test_complete_user_journey.py` (Backend - 40 tests)
1. **Registration & Email Verification** - Register, verify, login blocked before verification
2. **Job Import** - From LinkedIn URL, from description text
3. **Application Lifecycle** - Create, status transitions (saved→applied→screening→interview→offer), invalid transitions fail
4. **Notes CRUD** - Create, list (pinned first), update, delete
5. **Contacts CRUD** - Create, list (primary first), update, delete
6. **Timeline Events** - Status changes create events, user timeline across apps
7. **Audit Logging** - Status transitions logged
8. **Follow-up Reminders** - Set, list, clear
9. **Notifications** - Create, read, mark read, mark all read, unread count
10. **Analytics** - Overview, status breakdown, timeline, skills demand, market insights
11. **Resumes** - Create, list, get, export
12. **Cover Letters** - Create for application
13. **Batch Operations** - Create, list, get details
14. **User Isolation** - Users cannot access each other's data
15. **Rate Limiting** - Auth endpoints protected
16. **Token Refresh** - Refresh access token, logout
17. **Password Reset** - Forgot password, reset flow
18. **Full Workflow** - End-to-end: import job → apply → track → follow-up → notification → analytics
19. **Error Handling** - Invalid transitions, unauthorized, invalid imports, duplicates
20. **Pagination** - List endpoints respect limit/skip

### `complete-user-journey.spec.ts` (Frontend E2E - 12 test suites)
1. **Register & Verify Email** - Form validation, success redirect, resend verification
2. **Login & Dashboard** - Valid login, dashboard sections visible
3. **Job Import** - URL import (LinkedIn), description import, view history
4. **Application Tracking** - Create app, status transitions, notes, contacts, timeline
5. **Follow-up Center** - Set reminders, view center
6. **Notifications** - Bell icon, notifications page, mark read, mark all read
7. **Analytics Dashboard** - Overview, skills demand chart, market insights
8. **Resume Management** - Create profile, export PDF
9. **Cover Letters** - Generate for application
10. **Batch Operations** - Create batch job
11. **Settings & Profile** - Notification prefs, profile update
12. **Logout & Session** - Logout, session persistence

Plus existing E2E tests:
- `route-protection.spec.ts` - Auth guards, login/register pages accessible
- `job-import.spec.ts` - Import page UI, navigation
- `profile-editor.spec.ts` - Full profile editor (experience, education, skills, projects, certifications)
- `job-explorer.spec.ts` - Job browsing

## Requirements

**Backend:**
- Python 3.12+
- pytest, pytest-asyncio, httpx
- SQLite (test.db) - auto created
- Redis: Optional (uses memory fallback)

**Frontend E2E:**
- Node.js 18+
- Playwright
- Backend running on localhost:8000
- Frontend running on localhost:3030
- `VITE_API_URL=http://localhost:8000` (set in frontend/.env)

## Common Issues

1. **"Database locked"** - Ensure no other test processes running
2. **"Port 8000 in use"** - Kill existing uvicorn: `pkill -f uvicorn`
3. **"Playwright timeout"** - Increase timeout or check server is running
4. **"Redirect loop"** - Check `VITE_API_URL` matches backend URL
5. **Import errors** - Run `rtk pip install -r requirements-dev.txt` in backend