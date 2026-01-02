import smtplib
from email.message import EmailMessage
from app.config import settings


def send_lead_email(to_email: str, clinic_name: str, lead: dict):
    """Send a simple CRM-style lead notification email to the clinic."""
    if not to_email:
        return False

    msg = EmailMessage()
    msg['Subject'] = f"New lead from {clinic_name or 'Dental Bot'}"
    msg['From'] = settings.email_from
    msg['To'] = to_email
    body = f"New lead received:\n\nName: {lead.get('name')}\nPhone: {lead.get('phone')}\nEmail: {lead.get('email')}\nMessage: {lead.get('message')}\nSession: {lead.get('session_id')}\n"
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as s:
            s.starttls()
            if settings.smtp_user and settings.smtp_password:
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        return True
    except Exception:
        return False


def send_onboarding_email(to_email: str, clinic_name: str, snippet: str):
    if not to_email:
        return False
    msg = EmailMessage()
    msg['Subject'] = f"Welcome to Dental Bot — your embed snippet"
    msg['From'] = settings.email_from
    msg['To'] = to_email
    body = f"Hi {clinic_name or ''},\n\nThank you for onboarding. Paste the following snippet into your site's HTML to enable the chat widget:\n\n{snippet}\n\nIf you need help, reply to this email.\n"
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as s:
            s.starttls()
            if settings.smtp_user and settings.smtp_password:
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        return True
    except Exception:
        return False
