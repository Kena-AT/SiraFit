# SiraFit - Quick Start Guide

## Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL (or use Neon database)

## Backend Setup (FastAPI)

### 1. Navigate to backend directory
```cmd
cd backend
```

### 2. Create virtual environment
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```cmd
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the `backend` directory with:
```env
DATABASE_URL=postgresql://neondb_owner:npg_zoEByw26USid@ep-icy-block-ape62ltm-pooler.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
SECRET_KEY=14d02f6f9e9f4f8c8b9a7c3e2d1a0b5f6e4c3a2b1d0e9f8c7b6a5d4e3f2a1b0c
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=a4330f001@smtp-brevo.com
SMTP_PASSWORD=xsmtpsib-b3db4393a1edfbd3b1a8a63b09e01f2792c38fccd92ee2aad82d40387ad9196b-V7tLhf3lJvHHT6EE
SMTP_FROM=kenakaye11@gmail.com
PROJECT_NAME=SiraFit API
VERSION=1.0.0
API_V1_STR=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 5. Run database migrations
```cmd
alembic upgrade head
```

### 6. Start the backend server (Port 8000)
```cmd
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend will be running at:** http://localhost:8000
**API Documentation:** http://localhost:8000/docs

---

## Frontend Setup (Next.js)

### 1. Navigate to frontend directory
```cmd
cd frontend
```

### 2. Install dependencies
```cmd
npm install
```

### 3. Set up environment variables
Create a `.env.local` file in the `frontend` directory with:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Start the development server (Port 3000)
```cmd
npm run dev
```

**Frontend will be running at:** http://localhost:3000

---

## Using Docker Compose (Alternative)

### Start all services
```cmd
docker-compose up
```

This will start:
- Backend (FastAPI) - Port 8000
- Frontend (Next.js) - Port 3000  
- PostgreSQL - Port 5432
- Redis - Port 6379
- Celery Worker
- Celery Beat

---

## Available Pages

### Public Pages
- **Landing Page:** http://localhost:3000/
- **Login:** http://localhost:3000/login
- **Register:** http://localhost:3000/register
- **Forgot Password:** http://localhost:3000/forgot-password
- **Reset Password:** http://localhost:3000/reset-password?token=YOUR_TOKEN
- **Verify Email:** http://localhost:3000/verify-email?token=YOUR_TOKEN

### Protected Pages (Requires Authentication)
- **Dashboard:** http://localhost:3000/dashboard
- **Logout:** http://localhost:3000/logout

---

## Testing the Setup

### Test Backend
```cmd
curl http://localhost:8000/health
```

### Test Frontend
Open http://localhost:3000 in your browser

---

## Authentication Flow

1. **Register** - Create a new account at `/register`
2. **Verify Email** - Check your email and click the verification link
3. **Login** - Sign in at `/login`
4. **Access Dashboard** - You'll be redirected to `/dashboard`
5. **Logout** - Go to `/logout` to sign out

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (OAuth2 compatible)
- `POST /api/v1/auth/verify-email` - Verify email with token
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password with token
- `POST /api/v1/auth/refresh-token` - Refresh access token
- `POST /api/v1/auth/logout` - Logout and revoke refresh token

### User Profile
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile

---

## Troubleshooting

### Backend Issues
- **Database connection error:** Check DATABASE_URL in `.env`
- **Import errors:** Ensure virtual environment is activated
- **Port already in use:** Change port with `--port 8001`

### Frontend Issues
- **Module not found:** Run `npm install` again
- **Tailwind classes not working:** Delete `.next` folder and restart
- **API connection error:** Check NEXT_PUBLIC_API_URL in `.env.local`
- **Port 3000 in use:** Next.js will suggest an alternative port

### Common Fixes
```cmd
# Frontend: Clear cache and reinstall
cd frontend
rm -rf node_modules .next
npm install
npm run dev

# Backend: Recreate virtual environment
cd backend
rm -rf venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Development Commands

### Backend
```cmd
# Run tests
pytest tests/ -v

# Create new migration
alembic revision --autogenerate -m "description"

# Run specific migration
alembic upgrade head
```

### Frontend
```cmd
# Lint
npm run lint

# Type check
npx tsc --noEmit

# Production build
npm run build

# Start production server
npm start

# Run E2E tests
npm run test:e2e
```

---

## Sprint 1 Completion Status

✅ **Completed:**
- Backend FastAPI setup
- PostgreSQL integration (Neon)
- User authentication (register, login, logout)
- JWT access & refresh tokens
- Token revocation on logout
- Email verification flow
- Password reset flow
- User profile endpoints
- Structured error handling
- Logging middleware
- Frontend Next.js setup
- Design system with Tailwind CSS v4
- Authentication pages (login, register, forgot-password, reset-password, verify-email)
- Protected route handling
- User session management
- Dashboard layout shell
- Docker setup

🔧 **In Progress:**
- CI pipeline (needs test files)
- Database migrations (Alembic configured, needs migration files)

---

## Next Steps

1. Create database migration files with Alembic
2. Add API tests for authentication endpoints
3. Add frontend E2E tests with Playwright
4. Complete CI pipeline configuration
5. Implement dashboard features (job tracking, resume generation)
