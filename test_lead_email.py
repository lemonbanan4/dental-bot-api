import sys
import os

# Add project root to path to allow imports from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.email import send_lead_email
from app.config import settings

def run_test():
    print("--- Testing HTML Lead Email ---")
    print(f"SMTP Host: {settings.smtp_host}:{settings.smtp_port}")
    print(f"SMTP User: {settings.smtp_user}")
    print(f"Target Email: {settings.admin_email}")
    
    fake_lead = {
        "name": "Jane Doe",
        "phone": "+1 (555) 123-4567",
        "email": "jane.doe@example.com",
        "message": "I would like to book a consultation for teeth whitening. Do you have availability next Tuesday?",
        "session_id": "test-session-abc-123"
    }
    
    print("Sending...")
    success = send_lead_email(
        to_email=settings.admin_email,
        clinic_name="Lemon Dental Demo",
        lead=fake_lead,
        logo_url="https://via.placeholder.com/200x50?text=Lemon+Dental"
    )
    
    if success:
        print("✅ Success! Check your inbox for the HTML email.")
    else:
        print("❌ Failed to send email.")

if __name__ == "__main__":
    run_test()