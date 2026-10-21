import logging

import sentry_sdk

from app.core.config import settings

logger = logging.getLogger(__name__)


def init_sentry(component: str) -> bool:
    """Ativa o Sentry quando SENTRY_DSN está definido. `component` separa web e worker no painel."""
    if not settings.SENTRY_DSN:
        return False
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        # Não enviar e-mails, IPs, cookies nem corpo de requisição para terceiros (LGPD)
        send_default_pii=False,
        max_request_body_size="never",
    )
    sentry_sdk.set_tag("component", component)
    logger.info("Sentry ativado (%s, %s)", component, settings.ENVIRONMENT)
    return True
