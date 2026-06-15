# SiraFit - Quick Start

## 🚀 Start Backend (Port 8000)

```cmd
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ **Backend:** http://localhost:8000  
✅ **API Docs:** http://localhost:8000/docs

---

## 🎨 Start Frontend (Port 3030)

```cmd
cd frontend
npm run dev
```

✅ **Frontend:** http://localhost:3030

---

## 📧 Email Setup Required

Before registration/verification works, you need to configure email:

1. Read `EMAIL_SETUP.md` for detailed instructions
2. Choose an email provider (Brevo, Gmail, or SendGrid)
3. Update `backend/.env` with your SMTP credentials

**Quick Gmail Setup:**
1. Enable 2FA on your Google account
2. Generate app password: https://myaccount.google.com/apppasswords
3. Update `backend/.env`:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM=your-email@gmail.com
```

---

## ✅ Test the App

1. Open http://localhost:3030
2. Click "Create Account"
3. Register with your email
4. Check your inbox for verification email
5. Click the verification link
6. Login and access dashboard

---

## 🔧 Troubleshooting

**Backend won't start:**
- Check virtual environment is activated
- Check DATABASE_URL in backend/.env

**Frontend won't start:**
- Delete `.next` folder and restart
- Run `npm install` again

**Emails not sending:**
- Check SMTP credentials in backend/.env
- Read EMAIL_SETUP.md for provider-specific setup
- Check spam folder

**401 Unauthorized errors:**
- Backend and frontend must both be running
- Check CORS_ORIGINS in backend/.env includes http://localhost:3030
