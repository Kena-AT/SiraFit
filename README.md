# SiraFit

A full-stack job search automation platform with AI-powered resume management, application tracking, and intelligent job pipeline automation.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS v4 |
| Backend | Python 3.11+, FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL (Neon cloud) |
| Auth | JWT (access + refresh tokens), HttpOnly cookies |
| Email | Brevo SMTP (300 free emails/day) |
| Deployment | Vercel (frontend), Render (backend) |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm 9+
- Docker & Docker Compose 24+ (optional)

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd SiraFit
```

### 2. Start Backend (Terminal 1)

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend running at **http://localhost:8000** | API docs at **http://localhost:8000/docs**

### 3. Start Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Frontend running at **http://localhost:3030**

### Quick Start Script (PowerShell)

Create `start-dev.ps1`:

```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:3030"
```

---

## Port Configuration

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3030 | http://localhost:3030 |
| Backend API | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |
| PostgreSQL | Remote | Neon PostgreSQL (cloud) |
| SMTP | 587 | smtp-relay.brevo.com |

---

## Environment Variables

### Backend (`backend/.env`)

```
DATABASE_URL=postgresql://...
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your_smtp_user
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=your_email@gmail.com
PROJECT_NAME=SiraFit API
VERSION=1.0.0
API_V1_STR=/api/v1
CORS_ORIGINS=http://localhost:3030,http://localhost:8000
```

### Frontend (`frontend/.env.local`)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3030
```

---

## Email Configuration

Email verification and password reset require SMTP credentials. Choose one option:

### Option 1: Brevo (Recommended - Free 300 emails/day)

1. Sign up at https://app.brevo.com/
2. Go to Settings > SMTP & API
3. Copy SMTP login and generate a new SMTP key
4. Go to Senders > verify your sender email
5. Update `backend/.env`:
   ```
   SMTP_USER=<your_brevo_login>
   SMTP_PASSWORD=<your_smtp_key>
   SMTP_FROM=<your_verified_sender_email>
   ```

### Option 2: Gmail (Easiest)

1. Enable 2FA at https://myaccount.google.com/security
2. Get app password at https://myaccount.google.com/apppasswords
3. Select "Mail" and "Other device"
4. Update `backend/.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=<your_gmail_address>
   SMTP_PASSWORD=<16_character_app_password>
   SMTP_FROM=<your_gmail_address>
   ```

### Option 3: Development Mode (No real emails)

Skip SMTP setup entirely. Emails print to console, accounts auto-verify.

### Test email

```bash
cd backend
venv\Scripts\activate
python test_email.py
```

---

## API Reference

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe + DB status |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login (sets HttpOnly cookies) |
| POST | `/api/v1/auth/verify-email` | Verify email with token |
| POST | `/api/v1/auth/forgot-password` | Request password reset |
| POST | `/api/v1/auth/reset-password` | Reset password with token |
| POST | `/api/v1/auth/refresh-token` | Rotate access + refresh tokens |
| POST | `/api/v1/auth/logout` | Revoke token + clear cookies |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get authenticated user profile |
| PUT | `/api/v1/users/me` | Update user profile |

### Profiles (Resume)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/profiles/me` | Get or create user profile with all nested sections |
| PUT | `/api/v1/profiles/me` | Full monolithic update (replaces nested arrays) |

### Resumes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/resumes/` | List user resumes |
| POST | `/api/v1/resumes/` | Create a new resume |
| PUT | `/api/v1/resumes/{id}` | Update a resume |

---

## Database Migrations

```bash
cd backend
venv\Scripts\activate

alembic current              # Check current state
alembic upgrade head         # Apply pending migrations
alembic revision --autogenerate -m "describe change"  # Create new migration
alembic downgrade -1         # Roll back one step
alembic history              # Show migration history
```

---

## Testing

### Backend (Pytest)

```bash
cd backend
venv\Scripts\activate

pytest tests/ -v                                             # All tests
pytest tests/ -v --cov=app --cov-report=html                 # With coverage
pytest tests/test_profiles.py -v                             # Specific file
pytest tests/test_profiles.py::TestProfileEndpoints::test_update_profile_basic_fields -v  # Specific test
```

### Frontend E2E (Playwright)

```bash
cd frontend

npx playwright install --with-deps chromium   # First-time setup
npm run test:e2e                              # Run all E2E tests
npm run test:e2e:ui                           # Open Playwright UI
npm run test:e2e -- profile-editor.spec.ts    # Specific file
```

---

## Project Structure

```
SiraFit/
├── backend/
│   ├── app/
│   │   ├── api/                # Route handlers (auth, users, profiles, resumes)
│   │   ├── core/               # Config, DB, security, logging, middleware
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── services/           # Email service
│   ├── migrations/versions/    # Alembic migration scripts
│   ├── tests/                  # Pytest test suite
│   ├── render.yaml
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/     # Reusable UI components
│   │   │   ├── dashboard/      # Dashboard + protected pages
│   │   │   │   ├── resumes/    # Resume profiles list + editor
│   │   │   │   └── profile/    # User profile settings
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   ├── verify-email/
│   │   │   ├── forgot-password/
│   │   │   ├── reset-password/
│   │   │   └── logout/
│   │   ├── contexts/           # AuthContext (session management)
│   │   ├── lib/
│   │   │   ├── api/            # API functions (profiles, resumes)
│   │   │   └── validation/     # Client-side validation
│   │   ├── types/              # TypeScript type definitions
│   │   └── middleware.ts       # Route protection middleware
│   ├── e2e/                    # Playwright E2E tests
│   ├── playwright.config.ts
│   ├── next.config.mjs
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Reusable UI Components

| Component | Purpose |
|-----------|---------|
| `SectionCard` | Collapsible section wrapper with title and open/close toggle |
| `ArrayItem` | Row of fields for array items (experience, education, etc.) with remove button |
| `Input` | Styled text input with label, error display, character counter |
| `Textarea` | Styled textarea with label, error display, character counter |
| `ValidationDisplay` | Shows all validation errors in a banner |
| `StatusBadge` | Autosave status indicator (Ready / Saving... / Saved / Error) |

---

## Profile Editor Features

- **6 Sections**: Personal Information, Contact, Work Experience, Education, Skills, Projects, Certifications
- **Debounced Autosave**: 1-second delay, reduces API calls
- **Client-Side Validation**: Mirrors backend Pydantic schema constraints
- **Character Counters**: Shows current/max for length-limited fields
- **Collapsible Sections**: Expand/collapse each section independently
- **Add/Remove Items**: Dynamic array management with trash icon
- **Save Status**: Visual feedback (Saving... / Saved / Error)
- **Profile Isolation**: Users only see their own data

---

## Available Pages

### Public

| Page | URL | Description |
|------|-----|-------------|
| Landing | http://localhost:3030 | Marketing page |
| Login | http://localhost:3030/login | Sign in |
| Register | http://localhost:3030/register | Create account |
| Forgot Password | http://localhost:3030/forgot-password | Request reset link |
| Reset Password | http://localhost:3030/reset-password?token=... | Set new password |
| Verify Email | http://localhost:3030/verify-email?token=... | Verify account |

### Protected (Requires Authentication)

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | http://localhost:3030/dashboard | Main dashboard |
| Resumes | http://localhost:3030/dashboard/resumes | Resume profiles list |
| Resume Editor | http://localhost:3030/dashboard/resumes/[id]/editor | Profile editor |
| Profile | http://localhost:3030/dashboard/profile | User profile settings |
| Logout | http://localhost:3030/logout | Sign out |

---

## Deployment

### Frontend to Vercel

1. Push to GitHub
2. Connect repo to https://vercel.com
3. Set `NEXT_PUBLIC_API_URL` to your Render backend URL
4. Deploy

### Backend to Render

1. Connect repo to https://render.com
2. Select `backend/render.yaml` as configuration
3. Set secrets in Render dashboard:
   - `DATABASE_URL` -- your Neon PostgreSQL connection string
   - `SMTP_USER` -- your Brevo SMTP login
   - `SMTP_PASSWORD` -- your Brevo API key
4. Deploy

### Docker (Full Stack)

```bash
docker-compose up --build
```

Starts backend (8000), PostgreSQL (5432), Redis (6379), and Celery worker.

### Production Commands

```bash
# Frontend
cd frontend
npm run build && npm run start

# Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Common Issues & Troubleshooting

### Port already in use

```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
# Or use a different port
uvicorn app.main:app --reload --port 8001
```

### Module not found (Backend)

```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### Module not found (Frontend)

```bash
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### Database connection error

Check `DATABASE_URL` in `backend/.env`. Ensure Neon database is accessible and SSL mode is set correctly.

### CORS errors / 401 Unauthorized

Check `CORS_ORIGINS` in `backend/.env` includes `http://localhost:3030`. Restart backend after changes. Ensure frontend is on port 3030.

### Email not received

1. Check spam folder
2. Check backend console for errors
3. Run `python test_email.py` to test SMTP
4. Verify SMTP credentials in `backend/.env`

### Tailwind classes not working

```bash
cd frontend
Remove-Item -Recurse -Force .next
npm run dev
```

---

## Clean Up

```powershell
# Backend
cd backend
Remove-Item -Recurse -Force __pycache__, .pytest_cache, app/__pycache__, app/*/__pycache__

# Frontend
cd frontend
Remove-Item -Recurse -Force .next, node_modules
Remove-Item package-lock.json
```

---

## Security Notes

- Never commit `.env` files to git
- Change `SECRET_KEY` for production
- Use HTTPS in production
- Use app-specific passwords for SMTP (not your main password)
- Rotate SMTP keys periodically
- Use verified sender domains in production
- Monitor email sending limits (Brevo free tier: 300/day)
