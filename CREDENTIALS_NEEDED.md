# 📧 Email Credentials Needed

To make email verification work, please provide ONE of the following:

---

## Option 1: Brevo (Recommended)

**If you have a Brevo account**, provide:

```
SMTP_USER=_______________
SMTP_PASSWORD=_______________
SMTP_FROM=_______________
```

**How to get these:**
1. Login to https://app.brevo.com/
2. Go to Settings → SMTP & API
3. Copy your SMTP login and generate a new SMTP key
4. Go to Senders → verify your sender email

---

## Option 2: Gmail (Easiest)

**If you want to use Gmail**, provide:

```
Your Gmail address: _______________
App Password (16 chars): _______________
```

**How to get app password:**
1. Enable 2FA: https://myaccount.google.com/security
2. Get app password: https://myaccount.google.com/apppasswords
3. Select "Mail" and "Other device"
4. Copy the 16-character password

---

## Option 3: Other Service

**Tell me which service you want to use:**
- SendGrid
- Mailgun
- AWS SES
- Postmark
- Other

And I'll tell you what credentials I need.

---

## Option 4: Development Mode (Skip Emails)

If you just want to test without emails, I can configure the app to:
- Print email content to console
- Auto-verify all accounts
- Skip email sending entirely

**Choose this if:**
- You're just testing the app
- You'll configure real emails later
- You don't have email credentials yet

---

## ✅ Once You Provide Credentials

I will:
1. Update `backend/.env` with your credentials
2. Test the email service
3. Verify registration and password reset work
4. Confirm emails are being sent successfully

---

**Please reply with ONE of the options above and provide the required information.**
