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
        if settings.ENVIRONMENT in ("local", "test"):
            logger.warning("SMTP_HOST não configurado (modo dev). E-mail para %s:\n%s\n%s", to, subject, body)
        else:
            # Em homologação/produção o corpo (que pode ter links de redefinição) nunca vai para o log
            logger.error("SMTP_HOST não configurado; e-mail para %s não foi enviado", to)
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


if __name__ == "__main__":
    # Teste de configuração SMTP: python -m app.core.email voce@exemplo.com
    import sys

    if len(sys.argv) != 2:
        sys.exit("uso: python -m app.core.email destinatario@exemplo.com")
    test_message = EmailMessage()
    test_message["From"] = settings.SMTP_FROM
    test_message["To"] = sys.argv[1]
    test_message["Subject"] = f"Teste de e-mail - {settings.APP_NAME}"
    test_message.set_content("Se você recebeu esta mensagem, o SMTP está configurado corretamente.")
    _send_sync(test_message)  # sem try/except: o erro real aparece no terminal
    print(f"E-mail de teste enviado para {sys.argv[1]} via {settings.SMTP_HOST}:{settings.SMTP_PORT}")
