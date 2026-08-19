"""Optional transactional email integrations."""

import os

import requests


def _sender_email():
    """Use the configured Brevo sender, falling back to the SMTP login email."""
    return os.environ.get("BREVO_SENDER_EMAIL") or os.environ.get(
        "MAIL_USERNAME", "no-reply@havenandco.com"
    )


def _send_brevo_email(payload, code, recipient, label):
    """Send through Brevo and retain a useful local fallback on failure."""
    api_key = os.environ.get("BREVO_API_KEY")
    if not api_key:
        print(f"{label} for {recipient}: {code}")
        return False

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.HTTPError as exc:
        detail = response.text[:300].replace("\n", " ")
        print(f"Brevo rejected {label.lower()} for {recipient} (HTTP {response.status_code}): {detail}")
    except requests.RequestException as exc:
        print(f"Unable to send {label.lower()} for {recipient}: {exc}")

    print(f"{label} fallback for {recipient}: {code}")
    return False


def send_verification_email(user, code):
    """Send an email-verification code through Brevo or print it locally."""
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
    _send_brevo_email(payload, code, user.email, "Email verification code")


def send_password_reset_code_email(user, code):
    """Send a password-reset code through Brevo or print it locally."""
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
    _send_brevo_email(payload, code, user.email, "Password reset code")
