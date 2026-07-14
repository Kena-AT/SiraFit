# SiraFit

A full-stack job search automation platform designed to supercharge your career search. SiraFit combines AI-powered tools with a centralized dashboard to automate resume tailoring, track applications, and provide deep insights into your job search performance.

## 🚀 What is SiraFit?

SiraFit is your personal "Command Center" for job hunting. Instead of juggling spreadsheets and folders, SiraFit provides a unified workspace to:

- **Centralize Your Profile**: Maintain a master record of your experience, education, and skills.
- **Import Jobs Instantly**: One-click import from major platforms like LinkedIn, Indeed, and more.
- **AI Matching & Scoring**: Instantly see how well you match a job description and where the gaps are.
- **Generate Tailored Resumes**: Automatically create job-specific resumes and cover letters in seconds.
- **Track Every Application**: Manage your pipeline from initial application to final offer.
- **Actionable Analytics**: Visualize your conversion funnel and identify which skills are in high demand.

## ✨ Core Features

### 📝 Resume & Profile Management
- **Master Profile**: A robust editor to manage your entire professional history with autosave and real-time validation.
- **Smart Resume Builder**: Generate targeted resumes that highlight the specific skills each employer is looking for.
- **Cover Letter Generation**: AI-crafted cover letters that bridge the gap between your experience and the job requirements.

### 🔍 Intelligent Job Sourcing
- **Multi-Platform Import**: Scrape job details from LinkedIn, Glassdoor, ZipRecruiter, and more.
- **Manual Import**: Paste any job description to instantly extract key requirements.
- **Skill Extraction**: Automatically identifies required tech stacks and soft skills from job postings.

### 📊 Automation & Analytics
- **Application Tracking**: A structured pipeline to track interviews, follow-ups, and offers.
- **Insight Dashboard**: Monitor your application conversion rates and response times.
- **Market Intelligence**: Insights into market salary trends and the most sought-after skills in your niche.

### 🔔 Smart Notifications
- **Follow-up Reminders**: Never miss an opportunity to follow up after an interview.
- **Job Alerts**: Get notified when new matches are found or when applications need attention.

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19 (TanStack Start), TypeScript, Tailwind CSS v4 |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy, Pydantic |
| **Database** | PostgreSQL, Redis (for caching & background tasks) |
| **Worker** | Celery + Redis for asynchronous processing |
| **Auth** | Secure JWT with HttpOnly cookies & Refresh Tokens |
| **Email** | Brevo SMTP for notifications and verification |

---

## ⚡ Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Redis (for background workers)

### 1. Clone and configure
```bash
git clone <your-repo-url>
cd SiraFit
```

### 2. Start Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📖 Documentation Quick Links

- **Quick Start Guide**: `QUICK_REFERENCE.md` - Commands and setup tips.
- **Project Structure**: `PROJECT_STATUS_SUMMARY.md` - Architecture deep-dive.
- **API Reference**: Access the interactive docs at `http://localhost:8000/docs` when the backend is running.

---

## 🧪 Testing

### Backend
```bash
cd backend
pytest tests/
```

### Frontend
```bash
cd frontend
npm run test:e2e
```

---

## 🔐 Security Notes

- JWT tokens are handled securely via HttpOnly, SameSite, and Secure flags.
- Environment variables are strictly enforced (see `.env.example`).
- Full audit logs and background task monitoring integrated.
