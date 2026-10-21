import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_sync(message: EmailMessage) -> None:
    if not settings.SMTP_HOST:
        raise RuntimeError("SMTP_HOST não configurado")
    smtp_cls = smtplib.SMTP_SSL if settings.SMTP_SSL else smtplib.SMTP
    with smtp_cls(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        if settings.SMTP_STARTTLS and not settings.SMTP_SSL:
            smtp.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)


async def send_email(to: str, subject: str, body: str) -> None:
    """Envia um e-mail de texto via SMTP. Nunca levanta exceção: falhas vão para o log."""
    if not settings.SMTP_HOST:
        if settings.ENVIRONMENT == "production":
            logger.error("SMTP_HOST não configurado; e-mail para %s não foi enviado", to)
        else:
            logger.warning("SMTP_HOST não configurado (modo dev). E-mail para %s:\n%s\n%s", to, subject, body)
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        await asyncio.to_thread(_send_sync, message)
    except Exception:
        logger.exception("Falha ao enviar e-mail para %s", to)
