# SiraFit - Run Commands Guide

## Quick Start Guide

### Backend Setup

**1. Start Backend Server**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**2. Run Backend Migrations**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
```

**3. Run Backend Tests**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest tests/ -v
```

**4. Run Specific Test File**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest tests/test_profiles.py -v
```

### Frontend Setup

**1. Install Dependencies**
```powershell
cd frontend
npm install
```

**2. Start Frontend Development Server**
```powershell
cd frontend
npm run dev
# Server runs on http://localhost:3030
```

**3. Build Frontend for Production**
```powershell
cd frontend
npm run build
```

**4. Run Frontend E2E Tests**
```powershell
cd frontend
npm run test:e2e
```

**5. Run E2E Tests with UI**
```powershell
cd frontend
npm run test:e2e:ui
```

### Database Operations

**Generate New Migration**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic revision --autogenerate -m "description of changes"
```

**Apply Migrations**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
```

**Rollback Last Migration**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic downgrade -1
```

**Check Current Migration Version**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic current
```

**Show Migration History**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic history
```

### Testing & Verification

**Test Email Service**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python test_email.py
```

**Run All Backend Tests**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest tests/ -v --cov=app --cov-report=html
```

**Run Specific Test**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest tests/test_auth.py::TestAuthEndpoints::test_register -v
```

### Development Workflow

**Full Stack Development (Two Terminals)**

Terminal 1 - Backend:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Frontend:
```powershell
cd frontend
npm run dev
```

Then open: http://localhost:3030

### Port Information

- **Frontend**: http://localhost:3030
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

### Common Issues & Solutions

**Issue: Port already in use**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000
# Kill process by PID (replace <PID> with actual PID)
taskkill /PID <PID> /F

# Or use different port
uvicorn app.main:app --reload --port 8001
```

**Issue: Module not found (Backend)**
```powershell
# Make sure you're in virtual environment
cd backend
.\venv\Scripts\Activate.ps1
# Reinstall dependencies
pip install -r requirements.txt
```

**Issue: Module not found (Frontend)**
```powershell
# Delete node_modules and reinstall
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

**Issue: Database connection error**
- Check DATABASE_URL in backend/.env
- Ensure Neon database is accessible
- Verify SSL mode is set correctly

**Issue: CORS errors**
- Check CORS_ORIGINS in backend/.env includes http://localhost:3030
- Restart backend server after changes

### Environment Variables

**Backend (.env)**
```
DATABASE_URL=postgresql://...
SECRET_KEY=your_secret_key
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your_smtp_user
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=your_email@gmail.com
CORS_ORIGINS=http://localhost:3030,http://localhost:8000
```

**Frontend (.env.local)**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3030
```

### Git Commands

**Check status**
```powershell
git status
```

**Stage changes**
```powershell
git add .
```

**Commit changes**
```powershell
git commit -m "feat: implement sprint 2 profile editor"
```

**Push to remote**
```powershell
git push origin main
```

### Docker Commands (if using Docker Compose)

**Start all services**
```powershell
docker-compose up
```

**Start in detached mode**
```powershell
docker-compose up -d
```

**Stop all services**
```powershell
docker-compose down
```

**Rebuild containers**
```powershell
docker-compose up --build
```

**View logs**
```powershell
docker-compose logs -f
```

### Useful Shortcuts

**Backend + Frontend (PowerShell)**
Create a file `start-dev.ps1`:
```powershell
# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "Backend running on http://localhost:8000"
Write-Host "Frontend running on http://localhost:3030"
```

Then run:
```powershell
.\start-dev.ps1
```

### Clean Up

**Clean Backend**
```powershell
cd backend
Remove-Item -Recurse -Force __pycache__
Remove-Item -Recurse -Force .pytest_cache
Remove-Item -Recurse -Force app/__pycache__
Remove-Item -Recurse -Force app/*/__pycache__
```

**Clean Frontend**
```powershell
cd frontend
Remove-Item -Recurse -Force .next
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
```

### Production Deployment

**Build Frontend**
```powershell
cd frontend
npm run build
npm run start
```

**Run Backend (Production)**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Health Checks

**Check Backend Health**
```powershell
curl http://localhost:8000/health
```

**Check Frontend**
```powershell
curl http://localhost:3030
```

**Check Database Connection**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -c "from app.core.database import engine; engine.connect(); print('Database connected!')"
```

## Quick Reference

| Service | URL | Port |
|---------|-----|------|
| Frontend | http://localhost:3030 | 3030 |
| Backend API | http://localhost:8000 | 8000 |
| API Docs | http://localhost:8000/docs | 8000 |
| Database | Neon PostgreSQL | Remote |

## Sprint 2 Specific Commands

**Run Profile Migration**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
```

**Test Profile API**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest tests/test_profiles.py -v
```

**Test Profile Editor E2E**
```powershell
cd frontend
npm run test:e2e -- profile-editor.spec.ts
```

**Access Profile Editor**
1. Start both servers
2. Navigate to http://localhost:3030
3. Login with your credentials
4. Go to "Resumes" in sidebar
5. Click "Edit Profile"
