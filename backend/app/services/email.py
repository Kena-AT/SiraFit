import datetime
from pydantic import EmailStr
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class EmailService:
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM

    def _create_connection(self):
        """Create SMTP connection with STARTTLS"""
        server = smtplib.SMTP(self.host, self.port, timeout=5)
        server.ehlo()
        server.starttls()
        server.login(self.user, self.password)
        return server

    def send_email(
        self,
        to: EmailStr,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email using Brevo SMTP"""
        try:
            server = self._create_connection()
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"SiraFit Team <{self.from_email}>"
            msg["To"] = to

            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)
            
            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            server.sendmail(self.from_email, to, msg.as_string())
            server.quit()

            logger.info(
                "email_sent",
                to=to,
                subject=subject,
                service="brevo",
                success=True
            )
            return True

        except Exception as e:
            logger.error(
                "email_failed",
                to=to,
                subject=subject,
                error=str(e),
                service="brevo",
                success=False
            )
            return False

    def send_verification_email(self, email: EmailStr, token: str) -> bool:
        """Send email verification email"""
        verification_url = f"http://localhost:3030/verify-email?token={token}"
        subject = "Welcome to SiraFit - Verify Your Account"
        
        html_content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1px;">
          <div style="background: white; border-radius: 8px; padding: 40px; margin: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
            
            <!-- Header -->
            <div style="text-align: center; margin-bottom: 30px;">
              <div style="background: linear-gradient(135deg, #3525cd 0%, #667eea 100%); width: 80px; height: 80px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h8"></path>
                  <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                  <path d="m16 19 2 2 4-4"></path>
                </svg>
              </div>
              <h1 style="color: #1a202c; font-size: 28px; font-weight: 700; margin: 0 0 8px 0;">Welcome to SiraFit</h1>
              <p style="color: #718096; font-size: 16px; margin: 0;">High-density job search automation</p>
            </div>
            
            <!-- Content -->
            <div style="margin-bottom: 32px;">
              <h2 style="color: #2d3748; font-size: 20px; font-weight: 600; margin-bottom: 16px;">Let's get you started!</h2>
              <p style="color: #4a5568; line-height: 1.6; margin-bottom: 24px;">
                Thank you for joining SiraFit. We're excited to help automate your job search process. 
                First, let's verify your email address:
              </p>
              
              <!-- Verification Button -->
              <div style="text-align: center; margin: 32px 0;">
                <a href="{verification_url}" 
                   style="background: linear-gradient(135deg, #3525cd 0%, #667eea 100%); color: white; padding: 14px 32px; 
                          text-decoration: none; border-radius: 8px; display: inline-block; font-weight: 600;
                          font-size: 16px; transition: transform 0.2s;">
                  Verify Email Address
                </a>
              </div>
              
              <!-- Manual Link -->
              <div style="background: #f7fafc; border-radius: 6px; padding: 16px; margin-top: 24px;">
                <p style="color: #4a5568; font-size: 14px; margin: 0 0 8px 0; font-weight: 500;">Or copy and paste this link:</p>
                <a href="{verification_url}" style="color: #3525cd; font-size: 14px; word-break: break-all; text-decoration: none;">
                  {verification_url}
                </a>
              </div>
            </div>
            
            <!-- Footer -->
            <div style="border-top: 1px solid #e2e8f0; padding-top: 24px;">
              <p style="color: #a0aec0; font-size: 12px; margin: 0 0 8px 0;">
                This link will expire in 24 hours. If you didn't create a SiraFit account, you can safely ignore this email.
              </p>
              <p style="color: #a0aec0; font-size: 12px; margin: 0;">
                Need help? Contact our support team at support@sirafit.com
              </p>
            </div>
            
          </div>
          
          <!-- Company Footer -->
          <div style="text-align: center; padding: 20px;">
            <p style="color: rgba(255,255,255,0.9); font-size: 12px; margin: 0;">
              © {datetime.datetime.now().year} SiraFit Inc. All rights reserved.<br>
              High-density automation for job search
            </p>
          </div>
        </div>
        """
        
        return self.send_email(email, subject, html_content)

    def send_password_reset_email(self, email: EmailStr, token: str) -> bool:
        """Send password reset email"""
        reset_url = f"http://localhost:3030/reset-password?token={token}"
        subject = "SiraFit - Reset Your Password"
        
        html_content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1px;">
          <div style="background: white; border-radius: 8px; padding: 40px; margin: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
            
            <!-- Header -->
            <div style="text-align: center; margin-bottom: 30px;">
              <div style="background: linear-gradient(135deg, #e53e3e 0%, #f56565 100%); width: 80px; height: 80px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
                  <path d="M15.75 8.25a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
                  <path d="M4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
                </svg>
              </div>
              <h1 style="color: #1a202c; font-size: 28px; font-weight: 700; margin: 0 0 8px 0;">Password Reset</h1>
              <p style="color: #718096; font-size: 16px; margin: 0;">SiraFit Security Team</p>
            </div>
            
            <!-- Content -->
            <div style="margin-bottom: 32px;">
              <h2 style="color: #2d3748; font-size: 20px; font-weight: 600; margin-bottom: 16px;">Reset your password</h2>
              <p style="color: #4a5568; line-height: 1.6; margin-bottom: 24px;">
                We received a request to reset your SiraFit password. Click the button below to create a new password:
              </p>
              
              <!-- Reset Button -->
              <div style="text-align: center; margin: 32px 0;">
                <a href="{reset_url}" 
                   style="background: linear-gradient(135deg, #e53e3e 0%, #f56565 100%); color: white; padding: 14px 32px; 
                          text-decoration: none; border-radius: 8px; display: inline-block; font-weight: 600;
                          font-size: 16px; transition: transform 0.2s;">
                  Reset Password
                </a>
              </div>
              
              <!-- Manual Link -->
              <div style="background: #f7fafc; border-radius: 6px; padding: 16px; margin-top: 24px;">
                <p style="color: #4a5568; font-size: 14px; margin: 0 0 8px 0; font-weight: 500;">Or copy and paste this link:</p>
                <a href="{reset_url}" style="color: #3525cd; font-size: 14px; word-break: break-all; text-decoration: none;">
                  {reset_url}
                </a>
              </div>
              
              <div style="background: #fff5f5; border-left: 4px solid #fc8181; padding: 12px 16px; margin-top: 24px;">
                <p style="color: #c53030; font-size: 14px; margin: 0; font-weight: 500;">
                  ⚠️ This link expires in 24 hours.
                </p>
                <p style="color: #c53030; font-size: 14px; margin: 8px 0 0 0;">
                  If you didn't request this password reset, please ignore this email or contact our security team immediately.
                </p>
              </div>
            </div>
            
            <!-- Footer -->
            <div style="border-top: 1px solid #e2e8f0; padding-top: 24px;">
              <p style="color: #a0aec0; font-size: 12px; margin: 0 0 8px 0;">
                For security reasons, never share your password with anyone.
              </p>
              <p style="color: #a0aec0; font-size: 12px; margin: 0;">
                Security Team • SiraFit Inc.
              </p>
            </div>
            
          </div>
          
          <!-- Company Footer -->
          <div style="text-align: center; padding: 20px;">
            <p style="color: rgba(255,255,255,0.9); font-size: 12px; margin: 0;">
              © {datetime.datetime.now().year} SiraFit Inc. • Secure job search automation
            </p>
          </div>
        </div>
        """
        
        return self.send_email(email, subject, html_content)

    def send_application_update(
        self,
        email: EmailStr,
        job_title: str,
        company: str,
        new_status: str
    ) -> bool:
        """Send job application status update email"""
        subject = f"Update on your {job_title} application"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #3525cd;">Application Status Update</h2>
            <p>Your application for <strong>{job_title}</strong> at <strong>{company}</strong> has been updated:</p>
            <div style="background-color: #f5f5f5; padding: 16px; border-radius: 8px; margin: 16px 0;">
                <p style="margin: 0;"><strong>New Status:</strong> {new_status}</p>
            </div>
            <p>You can view all your applications and their status in your SiraFit dashboard.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 32px 0;">
            <p style="color: #999; font-size: 12px;">
                This is an automated message from SiraFit. Please do not reply to this email.
            </p>
        </div>
        """
        
        return self.send_email(email, subject, html_content)


# Email service instance
email_service = EmailService()
