# utils/email_sender.py
import smtplib
from email.message import EmailMessage

def send_via_smtp(host, port, user, password, to_email, subject, body, use_tls=True):
    """
    Sends a simple text email. Returns (True, None) on success, else (False, error).
    """
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to_email
        msg.set_content(body)
        with smtplib.SMTP(host, port, timeout=30) as s:
            if use_tls:
                s.starttls()
            if user and password:
                s.login(user, password)
            s.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)
