"""Semana 1: páginas legais, health check, Sentry e envio de e-mail por SMTP."""

import smtplib
from email.message import EmailMessage

import pytest

from app.core import email as email_module
from app.core import observability
from app.core.templates import templates

from .conftest import Client

LEGAL_PAGES = {
    "/termos": ["Termos de Uso", "Conteúdo gerado por IA", "art. 49 do Código de Defesa do Consumidor"],
    "/privacidade": ["Política de Privacidade", "LGPD", "OpenAI", "Asaas", "Encarregado", "art. 18"],
    "/exclusao-de-dados": ["Exclusão de Dados", "Integrações comerciais", "15 dias"],
}


@pytest.mark.parametrize("path", LEGAL_PAGES)
async def test_legal_pages_are_public(client: Client, path: str):
    resp = await client.get(path)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    for text in LEGAL_PAGES[path]:
        assert text in resp.text, f"{path} deveria conter {text!r}"


async def test_legal_pages_use_company_settings(client: Client, monkeypatch):
    monkeypatch.setitem(templates.env.globals["company"], "name", "Empresa Teste Ltda")
    monkeypatch.setitem(templates.env.globals["company"], "privacy_email", "dpo@empresa-teste.com")
    resp = await client.get("/privacidade")
    assert "Empresa Teste Ltda" in resp.text
    assert "mailto:dpo@empresa-teste.com" in resp.text


async def test_home_links_to_legal_pages(client: Client):
    resp = await client.get("/")
    for path in LEGAL_PAGES:
        assert f'href="{path}"' in resp.text
    assert "Ao criar a conta você concorda" in resp.text


async def test_health_checks_database(client: Client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "ok"}


async def test_health_returns_503_when_database_is_down(client: Client, monkeypatch):
    class BrokenSession:
        async def __aenter__(self):
            raise ConnectionError("banco fora do ar")

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr("app.main.AsyncSessionLocal", BrokenSession)
    resp = await client.get("/health")
    assert resp.status_code == 503
    assert resp.json()["database"] == "unavailable"


def test_sentry_is_disabled_without_dsn(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(observability.settings, "SENTRY_DSN", None)
    monkeypatch.setattr(observability.sentry_sdk, "init", lambda **kw: calls.append(kw))
    assert observability.init_sentry("web") is False
    assert calls == []


def test_sentry_init_does_not_send_personal_data(monkeypatch):
    calls: list[dict] = []
    tags: list[tuple[str, str]] = []
    monkeypatch.setattr(observability.settings, "SENTRY_DSN", "https://chave@o0.ingest.sentry.io/0")
    monkeypatch.setattr(observability.sentry_sdk, "init", lambda **kw: calls.append(kw))
    monkeypatch.setattr(observability.sentry_sdk, "set_tag", lambda k, v: tags.append((k, v)))

    assert observability.init_sentry("worker") is True
    assert calls[0]["dsn"] == "https://chave@o0.ingest.sentry.io/0"
    assert calls[0]["send_default_pii"] is False
    assert calls[0]["max_request_body_size"] == "never"
    assert ("component", "worker") in tags


class FakeSMTP:
    instances: list["FakeSMTP"] = []

    def __init__(self, host: str, port: int, timeout: int):
        self.host, self.port, self.timeout = host, port, timeout
        self.started_tls = False
        self.logged_in: tuple[str, str] | None = None
        self.sent: list[EmailMessage] = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, user: str, password: str):
        self.logged_in = (user, password)

    def send_message(self, message: EmailMessage):
        self.sent.append(message)


@pytest.fixture
def smtp_settings(monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    for key, value in {
        "SMTP_HOST": "smtp-relay.brevo.com",
        "SMTP_PORT": 587,
        "SMTP_USER": "usuario",
        "SMTP_PASSWORD": "chave-smtp",
        "SMTP_FROM": "Prosolution <no-reply@exemplo.com>",
        "SMTP_STARTTLS": True,
        "SMTP_SSL": False,
    }.items():
        monkeypatch.setattr(email_module.settings, key, value)


async def test_send_email_uses_starttls_and_login(smtp_settings):
    await email_module.send_email("cliente@exemplo.com", "Assunto", "Corpo do e-mail")

    smtp = FakeSMTP.instances[0]
    assert (smtp.host, smtp.port) == ("smtp-relay.brevo.com", 587)
    assert smtp.started_tls
    assert smtp.logged_in == ("usuario", "chave-smtp")
    message = smtp.sent[0]
    assert message["To"] == "cliente@exemplo.com"
    assert message["From"] == "Prosolution <no-reply@exemplo.com>"
    assert message["Subject"] == "Assunto"
    assert "Corpo do e-mail" in message.get_content()


async def test_send_email_failure_is_logged_not_raised(smtp_settings, monkeypatch, caplog):
    def explode(self, message):
        raise smtplib.SMTPAuthenticationError(535, b"credenciais invalidas")

    monkeypatch.setattr(FakeSMTP, "send_message", explode)
    await email_module.send_email("cliente@exemplo.com", "Assunto", "Corpo")
    assert "Falha ao enviar e-mail" in caplog.text


async def test_password_recovery_sends_real_email_through_smtp(client: Client, smtp_settings):
    """Fluxo completo: o pedido na tela vira um e-mail SMTP com o link de redefinição."""
    await client.register("smtp@exemplo.com")
    resp = await client.submit("/auth/recover-password", {"email": "smtp@exemplo.com"})
    assert resp.status_code == 200

    sent = [m for smtp in FakeSMTP.instances for m in smtp.sent]
    assert len(sent) == 1
    assert sent[0]["To"] == "smtp@exemplo.com"
    assert "/auth/reset-password?token=" in sent[0].get_content()


async def test_head_requests_work_for_uptime_monitors(client: Client):
    assert (await client.head("/")).status_code == 200
    assert (await client.head("/health")).status_code == 200


@pytest.mark.parametrize("environment", ["staging", "production"])
async def test_email_body_is_never_logged_outside_dev(monkeypatch, caplog, environment: str):
    monkeypatch.setattr(email_module.settings, "SMTP_HOST", None)
    monkeypatch.setattr(email_module.settings, "ENVIRONMENT", environment)
    await email_module.send_email("a@exemplo.com", "Assunto", "link secreto https://x/reset?token=abc")
    assert "token=abc" not in caplog.text
    assert "não foi enviado" in caplog.text
