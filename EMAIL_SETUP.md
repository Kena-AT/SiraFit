# Email Service Setup Guide

For email verification and password reset to work, you need to configure SMTP credentials.

## Current Configuration

Your backend `.env` file currently has these placeholder values:

```env
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your_brevo_smtp_login
SMTP_PASSWORD=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
SMTP_FROM=noreply@sirafit.com
```

## Option 1: Brevo (Recommended - Free Tier: 300 emails/day)

### Step 1: Create Brevo Account
1. Go to https://app.brevo.com/
2. Sign up for a free account
3. Verify your email address

### Step 2: Get SMTP Credentials
1. Log in to Brevo dashboard
2. Go to **Settings** → **SMTP & API**
3. Click on **SMTP** tab
4. You'll see:
   - **SMTP Server**: smtp-relay.brevo.com
   - **Port**: 587
   - **Login**: Your email or SMTP login
   - **SMTP Key**: Click "Generate a new SMTP key"

### Step 3: Verify Sender Email
1. Go to **Senders** → **Domains & Addresses**
2. Add and verify your sender email (e.g., noreply@yourdomain.com or use your Brevo email)

### Step 4: Update Backend .env
Replace in `backend/.env`:
```env
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=<your_brevo_login_or_email>
SMTP_PASSWORD=<your_smtp_key_from_brevo>
SMTP_FROM=<your_verified_sender_email>
```

---

## Option 2: Gmail (Free - Easy Setup)

### Step 1: Enable 2-Factor Authentication
1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification**

### Step 2: Create App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select app: **Mail**
3. Select device: **Other** (enter "SiraFit")
4. Click **Generate**
5. Copy the 16-character password

### Step 3: Update Backend .env
Replace in `backend/.env`:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your_gmail_address>
SMTP_PASSWORD=<16_character_app_password>
SMTP_FROM=<your_gmail_address>
```

---

## Option 3: SendGrid (Free Tier: 100 emails/day)

### Step 1: Create SendGrid Account
1. Go to https://signup.sendgrid.com/
2. Sign up for free account

### Step 2: Create API Key
1. Go to **Settings** → **API Keys**
2. Click **Create API Key**
3. Give it a name and select **Full Access**
4. Copy the API key

### Step 3: Verify Sender
1. Go to **Settings** → **Sender Authentication**
2. Verify a single sender email

### Step 4: Update Backend .env
Replace in `backend/.env`:
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<your_sendgrid_api_key>
SMTP_FROM=<your_verified_sender_email>
```

---

## Testing Email Configuration

After updating your `.env` file, test the email service:

### 1. Restart Backend
```cmd
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Register a New User
1. Open http://localhost:3030/register
2. Fill in your email address
3. Submit the form

### 3. Check Email
- Check your inbox (and spam folder)
- You should receive a verification email
- Click the link to verify your account

---

## Troubleshooting

### Issue: "Authentication failed"
**Cause**: Wrong SMTP credentials  
**Solution**: Double-check username and password in `.env`

### Issue: "Connection refused"
**Cause**: Wrong SMTP host or port  
**Solution**: Verify SMTP_HOST and SMTP_PORT match your provider

### Issue: "Email not received"
**Causes**:
- Email in spam folder → Check spam
- Sender not verified → Verify sender email with provider
- Daily limit reached → Check provider dashboard

### Issue: "SSL/TLS error"
**Cause**: Port/encryption mismatch  
**Solution**: Use port 587 with STARTTLS (current setup)

---

## Development Mode (No Emails)

If you want to test without sending real emails, you can use console logging:

### Update `backend/app/services/email.py`:

Replace the `send_email` method with:
```python
def send_email(self, to: EmailStr, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
    """Send email to console (development mode)"""
    print("=" * 50)
    print(f"TO: {to}")
    print(f"SUBJECT: {subject}")
    print(f"BODY:\n{html_content}")
    print("=" * 50)
    return True
```

This will print emails to the console instead of sending them.

---

## Security Best Practices

1. ✅ Never commit `.env` files to git
2. ✅ Use app-specific passwords (not your main password)
3. ✅ Rotate SMTP keys periodically
4. ✅ Use verified sender domains in production
5. ✅ Monitor email sending limits and quotas
