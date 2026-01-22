
import smtplib
from email.message import EmailMessage
from app.config import settings
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
from typing import Optional


_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')
_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)


def _render_template(name: str, context: dict) -> str:
    tpl = _env.get_template(name)
    return tpl.render(**context)


def _send_message(msg: EmailMessage) -> bool:
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as s:
            s.starttls()
            if settings.smtp_user and settings.smtp_password:
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        return True
    except Exception:
        return False


def send_lead_email(to_email: str, clinic_name: str, lead: dict, logo_url: Optional[str] = None, theme: Optional[str] = None):
    """Send a CRM-style lead notification email (HTML + plain-text fallback)."""
    if not to_email:
        return False

    html = _render_template('lead_email.html', { 'clinic_name': clinic_name, 'lead': lead, 'logo_url': logo_url, 'theme': theme })
    text = f"New lead: {lead.get('name')} — {lead.get('phone')} — {lead.get('email')}\nMessage: {lead.get('message')}"

    msg = EmailMessage()
    msg['Subject'] = f"New lead from {clinic_name or 'Dental Bot'}"
    msg['From'] = settings.email_from
    msg['To'] = to_email
    msg.set_content(text)
    msg.add_alternative(html, subtype='html')

    return _send_message(msg)

def send_onboarding_email(to_email: str, clinic_name: str, snippet: str, logo_url: Optional[str] = None, preview_text: Optional[str] = None):
    if not to_email:
        return False

    html = _render_template('onboarding_email.html', { 'clinic_name': clinic_name, 'snippet': snippet, 'logo_url': logo_url, 'preview_text': preview_text })
    text = f"Welcome to Dental Bot. Paste this snippet into your site's HTML:\n\n{snippet}\n"

    msg = EmailMessage()
    msg['Subject'] = f"Welcome to Dental Bot — your embed snippet"
    msg['From'] = settings.email_from
    msg['To'] = to_email
    msg.set_content(text)
    msg.add_alternative(html, subtype='html')

    return _send_message(msg)
