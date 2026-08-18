"""Optional transactional email integrations."""

import os

import requests


def _sender_email():
    """Use the configured Brevo sender, falling back to the SMTP login email."""
    return os.environ.get("BREVO_SENDER_EMAIL") or os.environ.get(
        "MAIL_USERNAME", "no-reply@havenandco.com"
    )


def send_verification_email(user, code):
    """Send an email-verification code through Brevo or print it locally."""
    api_key = os.environ.get("BREVO_API_KEY")
    if not api_key:
        print(f"Email verification code for {user.email}: {code}")
        return

    sender_email = _sender_email()
    payload = {
        "sender": {"name": "Haven & Co.", "email": sender_email},
        "to": [{"email": user.email, "name": user.name}],
        "subject": "Your Haven & Co. verification code",
        "htmlContent": (
            "<p>Use this code to verify your Haven &amp; Co. email address:</p>"
            f"<p><strong style=\"font-size: 24px; letter-spacing: 4px;\">{code}</strong></p>"
            "<p>This code expires in 15 minutes.</p>"
        ),
    }
    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Unable to send email-verification code for {user.email}: {exc}")


def send_password_reset_code_email(user, code):
    """Send a password-reset code through Brevo or print it locally."""
    api_key = os.environ.get("BREVO_API_KEY")
    if not api_key:
        print(f"Password reset code for {user.email}: {code}")
        return

    sender_email = _sender_email()
    payload = {
        "sender": {"name": "Haven & Co.", "email": sender_email},
        "to": [{"email": user.email, "name": user.name}],
        "subject": "Your Haven & Co. password reset code",
        "htmlContent": (
            "<p>Use this code to reset your Haven &amp; Co. password:</p>"
            f"<p><strong style=\"font-size: 24px; letter-spacing: 4px;\">{code}</strong></p>"
            "<p>This code expires in 15 minutes.</p>"
            "<p>If you didn't request this, you can safely ignore this email.</p>"
        ),
    }
    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Unable to send password-reset code for {user.email}: {exc}")
