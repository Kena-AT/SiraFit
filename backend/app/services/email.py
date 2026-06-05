from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List, Optional
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
        server = smtplib.SMTP(self.host, self.port)
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
            msg["From"] = self.from_email
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
        verification_url = f"http://localhost:3000/verify-email?token={token}"
        subject = "Verify your SiraFit account"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #3525cd;">Welcome to SiraFit!</h2>
            <p>Thank you for registering. Please verify your email address to get started:</p>
            <a href="{verification_url}" 
               style="background-color: #3525cd; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 6px; display: inline-block;
                      margin: 16px 0;">
                Verify Email
            </a>
            <p style="color: #666; font-size: 14px;">
                Or copy and paste this link into your browser:<br>
                <a href="{verification_url}">{verification_url}</a>
            </p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 32px 0;">
            <p style="color: #999; font-size: 12px;">
                If you didn't create a SiraFit account, you can safely ignore this email.
            </p>
        </div>
        """
        
        return self.send_email(email, subject, html_content)

    def send_password_reset_email(self, email: EmailStr, token: str) -> bool:
        """Send password reset email"""
        reset_url = f"http://localhost:3000/reset-password?token={token}"
        subject = "Reset your SiraFit password"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #3525cd;">Password Reset Request</h2>
            <p>You requested to reset your password. Click the button below to proceed:</p>
            <a href="{reset_url}" 
               style="background-color: #3525cd; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 6px; display: inline-block;
                      margin: 16px 0;">
                Reset Password
            </a>
            <p style="color: #666; font-size: 14px;">
                Or copy and paste this link into your browser:<br>
                <a href="{reset_url}">{reset_url}</a>
            </p>
            <p style="color: #999; font-size: 12px;">
                This link will expire in 24 hours.<br>
                If you didn't request a password reset, you can safely ignore this email.
            </p>
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
