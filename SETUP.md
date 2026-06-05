# SiraFit Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+ with npm
- Docker & Docker Compose (for full stack)

## Environment Setup

### Backend

1. Copy the example `.env` file in the backend directory
2. Update the database connection string with your Neon PostgreSQL URL
3. Update the SMTP password with your Brevo API key

```bash
cd backend
cp .env.example .env
```

### Frontend

1. Copy the example `.env.local` file
2. Update the API URL if needed

```bash
cp .env.local.example .env.local
```

## Development Setup

### Option 1: Full Stack with Docker (Recommended)

```bash
docker-compose up --build
```

### Option 2: Manual Setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
SiraFit/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core utilities (config, security, logging)
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic (email, etc.)
│   ├── migrations/       # Alembic migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js app router pages
│   │   └── contexts/     # React contexts (auth, etc.)
│   └── package.json
└── docker-compose.yml
```

## API Endpoints

### Health Checks
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe with database status

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/verify-email` - Verify email
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password
- `POST /api/v1/auth/refresh-token` - Refresh access token

### Users
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update current user

## Features Implemented

- User registration with email verification
- Login with JWT tokens
- Password reset flow
- Structured logging with correlation IDs
- Health check endpoints
- Docker Compose setup
- PostgreSQL database with Alembic migrations
- Redis cache support
- Celery workers for background tasks
- Brevo SMTP email service
- Audit logging for auth events
