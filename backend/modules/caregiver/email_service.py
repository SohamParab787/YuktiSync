"""Email delivery for caregiver invitations."""

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)


def is_email_configured() -> bool:
    return all((settings.SMTP_HOST, settings.SMTP_USERNAME, settings.SMTP_PASSWORD, settings.SMTP_FROM_EMAIL))


def _send_invite_email(to_email: str, caregiver_name: Optional[str], patient_name: str, invite_url: str, expires_in_days: int) -> None:
    message = EmailMessage()
    message["Subject"] = f"YuktiSync caregiver invitation from {patient_name}"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email
    greeting = f"Hello {caregiver_name}," if caregiver_name else "Hello,"
    message.set_content(
        f"{greeting}\n\n{patient_name} invited you to connect as a caregiver on YuktiSync.\n\n"
        f"Accept the invitation using this link (it expires in {expires_in_days} days):\n{invite_url}\n\n"
        "If you were not expecting this invitation, you can ignore this email."
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)


async def send_invite_email(to_email: str, caregiver_name: Optional[str], patient_name: str, invite_url: str, expires_in_days: int) -> bool:
    """Return False when mail is not configured; otherwise deliver via SMTP."""
    if not is_email_configured():
        logger.warning("Caregiver invite email not sent: SMTP settings are incomplete")
        return False
    try:
        await asyncio.to_thread(_send_invite_email, to_email, caregiver_name, patient_name, invite_url, expires_in_days)
        return True
    except (OSError, smtplib.SMTPException) as exc:
        logger.exception("Could not send caregiver invitation email to %s", to_email)
        raise RuntimeError("The invitation was created, but the email could not be sent. Check SMTP settings.") from exc
