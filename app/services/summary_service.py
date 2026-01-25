import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from app.config import settings
from app.supabase_db import get_feedback_counts

def send_weekly_summary_email(target_email: str):
    """Generates and sends a weekly feedback summary email."""
    # 1. Calculate Date Range (Last 7 Days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    # 2. Fetch Data
    stats = get_feedback_counts(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    
    if not stats:
        print("No feedback data found for weekly summary.")
        return

    # 3. Format Email Content (HTML)
    html_content = f"""
    <html>
    <body>
        <h2>Weekly Feedback Summary</h2>
        <p><strong>Period:</strong> {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}</p>
        <table border="1" cellpadding="5" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th style="text-align: left;">Clinic Name</th>
                <th style="text-align: center;">👍 Up</th>
                <th style="text-align: center;">👎 Down</th>
                <th style="text-align: center;">Total</th>
            </tr>
    """
    
    for row in stats:
        clinic_name = row.get('clinic_name') or 'Unknown'
        up = row.get('up', 0)
        down = row.get('down', 0)
        total = row.get('total', 0)
        
        html_content += f"""
            <tr>
                <td>{clinic_name}</td>
                <td style="text-align: center; color: green;">{up}</td>
                <td style="text-align: center; color: red;">{down}</td>
                <td style="text-align: center;"><strong>{total}</strong></td>
            </tr>
        """
        
    html_content += """
        </table>
        <p><em>Sent by Dental Bot API</em></p>
    </body>
    </html>
    """

    # 4. Send Email
    msg = MIMEMultipart()
    msg['From'] = settings.email_from
    msg['To'] = target_email
    msg['Subject'] = f"Weekly Feedback Summary - {end_date.strftime('%Y-%m-%d')}"
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"Weekly summary email sent to {target_email}")
    except Exception as e:
        print(f"Failed to send summary email: {e}")