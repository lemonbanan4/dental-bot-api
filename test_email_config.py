import smtplib
from email.mime.text import MIMEText
from app.config import settings

def test_smtp():
    print("--- SMTP Configuration Test ---")
    print(f"SMTP Host: {settings.smtp_host}")
    print(f"SMTP Port: {settings.smtp_port}")
    print(f"SMTP User: {settings.smtp_user}")
    print(f"Email From: {settings.email_from}")
    print(f"Sending test email to: {settings.admin_email}")
    print("-------------------------------")

    msg = MIMEText("If you are reading this, your Dental Bot email configuration is working correctly!")
    msg['Subject'] = "Dental Bot: SMTP Configuration Test"
    msg['From'] = settings.email_from
    msg['To'] = settings.admin_email

    try:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        print("\n✅ SUCCESS: Test email sent successfully!")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        print("\nTip: If using Google Workspace, ensure you are using the App Password for info@lemontechno.org, not your login password.")

if __name__ == "__main__":
    test_smtp()