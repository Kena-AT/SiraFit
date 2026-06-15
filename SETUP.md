# SiraFit — Developer Setup Guide

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| Docker & Docker Compose | 24+ (optional, for full stack) |

---

## 1. Clone & Configure Environment

```bash
# Clone the repo
git clone <your-repo-url>
cd SiraFit
```

### Backend `.env`
The `backend/.env` file is already configured for Neon PostgreSQL.
You only need to set the Brevo SMTP credentials:

```
SMTP_USER=<your-brevo-login-email>
SMTP_PASSWORD=<your-brevo-api-key>
```

### Frontend `.env.local`
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 2. Running Locally (Manual — Recommended for Development)

Open **two terminals**.

### Terminal 1 — Backend (FastAPI)

```bash
# From the project root, create & activate the virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Run database migrations (first time only, or after schema changes)
cd backend
alembic upgrade head

# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend is now running at → **http://localhost:8000**  
API docs (Swagger) → **http://localhost:8000/docs**

### Terminal 2 — Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Frontend is now running at → **http://localhost:3030**

---

## 3. Running with Docker (Full Stack)

```bash
# From the project root
docker-compose up --build
```

This starts:
- **Backend** on port `8000`
- **PostgreSQL** on port `5432`
- **Redis** on port `6379`
- **Celery Worker** (background tasks)

---

## 4. Running Tests

### Backend Tests (Pytest)

```bash
# Activate venv first, then:
cd backend
python -m pytest tests/ -v
```

### Frontend E2E Tests (Playwright)

```bash
cd frontend

# First-time setup: install browsers
npx playwright install --with-deps chromium

# Run E2E tests (requires backend to be running on :8000)
npm run test:e2e

# Open Playwright UI for interactive debugging
npm run test:e2e:ui
```

---

## 5. Database Migrations

```bash
cd backend

# Check current migration state
alembic current

# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Roll back one step
alembic downgrade -1
```

---

## 6. Project Structure

```
SiraFit/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI pipeline
├── backend/
│   ├── app/
│   │   ├── api/                # Route handlers (auth, users)
│   │   ├── core/               # Config, DB, security, logging, middleware
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── services/           # Email service
│   ├── migrations/             # Alembic migration files
│   ├── tests/                  # Pytest test suite
│   ├── render.yaml             # Render staging deployment config
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js App Router pages
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   ├── verify-email/
│   │   │   ├── forgot-password/
│   │   │   ├── reset-password/
│   │   │   ├── logout/
│   │   │   └── dashboard/
│   │   ├── contexts/           # AuthContext (session management)
│   │   └── middleware.ts       # Route protection middleware
│   ├── e2e/                    # Playwright E2E tests
│   ├── playwright.config.ts
│   ├── next.config.mjs         # API rewrite proxy
│   ├── vercel.json             # Vercel staging deployment config
│   └── package.json
└── docker-compose.yml
```

---

## 7. API Reference

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

---

## 8. Staging Deployment

### Frontend → Vercel
1. Push to GitHub
2. Connect repo to [vercel.com](https://vercel.com)
3. Set `NEXT_PUBLIC_API_URL` to your Render backend URL
4. Deploy

### Backend → Render
1. Connect repo to [render.com](https://render.com)
2. Select `backend/render.yaml` as the configuration
3. Set the following secrets in the Render dashboard:
   - `DATABASE_URL` — your Neon PostgreSQL connection string
   - `SMTP_USER` — your Brevo SMTP login
   - `SMTP_PASSWORD` — your Brevo API key
4. Deploy
