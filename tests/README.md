# Test Suite Directory

This directory contains comprehensive end-to-end and integration tests for the SiraFit application.

## Structure

```
tests/
├── complete-user-journey.spec.ts     # Frontend E2E tests (Playwright)
├── backend/
│   └── test_complete_user_journey.py # Backend integration tests (pytest)
└── README.md                         # This file
```

## Running Tests

### Backend Integration Tests (pytest)

```bash
cd backend

# Install dev dependencies
rtk pip install -r requirements-dev.txt

# Run all journey tests
rtk pytest tests/test_complete_user_journey.py -v

# Run specific test class
rtk pytest tests/test_complete_user_journey.py::TestCompleteUserJourney -v

# Run specific test
rtk pytest tests/test_complete_user_journey.py::TestCompleteUserJourney::test_20_full_application_workflow -v

# Run with coverage
rtk pytest tests/test_complete_user_journey.py --cov=app --cov-report=term-missing
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

# Run E2E tests (Terminal 3)
cd tests && rtk npx playwright test complete-user-journey.spec.ts --headed

# Run with HTML report
rtk npx playwright test complete-user-journey.spec.ts --reporter=html
rtk npx playwright show-report
```

### Combined Test Run

1. Start backend: `cd backend && rtk python -m uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && rtk pnpm dev`
3. Run E2E: `cd tests && rtk npx playwright test complete-user-journey.spec.ts`

## Test Coverage

The test suite covers the complete user journey:

1. **Registration & Email Verification**
   - Register new user
   - Verify email (resend link)
   - Login blocked before verification

2. **Login & Dashboard**
   - Valid credentials login
   - Dashboard access and sections

3. **Job Management**
   - Import from LinkedIn URL
   - Import from description text
   - View import history

4. **Application Tracking**
   - Create application
   - Status transitions (saved → applied → screening → interview → offer)
   - Notes CRUD (create, list, update, delete, pin)
   - Contacts CRUD (create, list, update, delete, primary)
   - Timeline events
   - Audit logging

5. **Follow-up Center**
   - Set follow-up reminders
   - View upcoming follow-ups

6. **Notifications**
   - Create notifications
   - Mark as read / Mark all as read
   - Unread count
   - Filter by status

7. **Analytics Dashboard**
   - Overview metrics
   - Skills demand chart
   - Market insights

8. **Resume Management**
   - Create/edit profile
   - Export PDF

9. **Cover Letters**
   - Generate for application

10. **Batch Operations**
    - Create batch jobs

11. **Settings & Profile**
    - Notification preferences
    - Profile updates

12. **Session Management**
    - Logout
    - Session persistence

13. **Security & Edge Cases**
    - User data isolation
    - Rate limiting
    - Invalid transitions
    - Unauthorized access
    - Password reset flow

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
2. **"Port 8000 in use"** - Kill existing uvicorn processes: `pkill -f uvicorn`
3. **"Playwright timeout"** - Increase timeout or check server is running
4. **"Redirect loop"** - Check `VITE_API_URL` matches backend URL
5. **Import errors** - Run `rtk pip install -r requirements-dev.txt` in backend