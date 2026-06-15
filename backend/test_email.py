"""
Simple script to test email configuration
Run: python test_email.py
"""
import os
from dotenv import load_dotenv
from app.services.email import email_service

# Load environment variables
load_dotenv()

def test_email():
    """Test sending a verification email"""
    test_email_address = "kenakaye11@gmail.com"  # Send to yourself for testing
    test_token = "test_token_12345"
    
    print("=" * 60)
    print("Testing Email Configuration")
    print("=" * 60)
    print(f"SMTP Host: {os.getenv('SMTP_HOST')}")
    print(f"SMTP Port: {os.getenv('SMTP_PORT')}")
    print(f"SMTP User: {os.getenv('SMTP_USER')}")
    print(f"SMTP From: {os.getenv('SMTP_FROM')}")
    print(f"Sending test email to: {test_email_address}")
    print("=" * 60)
    
    try:
        result = email_service.send_verification_email(test_email_address, test_token)
        
        if result:
            print("\n✅ SUCCESS! Email sent successfully!")
            print(f"\nCheck your inbox at {test_email_address}")
            print("(Also check spam folder)")
            print("\nVerification link in email:")
            print(f"http://localhost:3030/verify-email?token={test_token}")
        else:
            print("\n❌ FAILED! Email could not be sent.")
            print("Check the error messages above.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nCommon issues:")
        print("1. Wrong SMTP credentials")
        print("2. Sender email not verified in Brevo")
        print("3. Network/firewall blocking SMTP")

if __name__ == "__main__":
    test_email()
