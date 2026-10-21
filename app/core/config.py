from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração única da aplicação, carregada do ambiente / arquivo .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # === APP ===
    APP_NAME: str = "Prosolution IA"
    ENVIRONMENT: str = "local"
    APP_BASE_URL: str = "http://localhost:3000"
    APP_TIMEZONE: str = "America/Sao_Paulo"

    # === SEGURANÇA (obrigatórias, sem fallback) ===
    SECRET_KEY: str
    ENCRYPTION_KEY: str  # chave Fernet usada para criptografar tokens de terceiros no banco
    TOKEN_EXPIRES_HOURS: int = 2
    PASSWORD_RESET_EXPIRES_MINUTES: int = 15
    COOKIE_SECURE: bool = True

    # === RATE LIMIT ===
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_STORAGE_URI: str = "memory://"  # use redis://... com mais de um processo/réplica
    LOGIN_RATE_LIMIT: str = "5/minute"
    REGISTER_RATE_LIMIT: str = "5/minute"
    RECOVER_PASSWORD_RATE_LIMIT: str = "3/minute"  # noqa: S105 (não é senha)

    # === DATABASE ===
    DATABASE_URL: str = "sqlite+aiosqlite:///./prosolution.db"

    # === E-MAIL (SMTP) ===
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "Prosolution <no-reply@prosolution.local>"
    SMTP_STARTTLS: bool = True
    SMTP_SSL: bool = False

    # === IA ===
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # === INSTAGRAM / META ===
    INSTAGRAM_APP_ID: str | None = None
    INSTAGRAM_APP_SECRET: str | None = None
    INSTAGRAM_REDIRECT_URI: str | None = None
    INSTAGRAM_GRAPH_URL: str = "https://graph.facebook.com"
    INSTAGRAM_API_VERSION: str = "v24.0"

    # === ASAAS (pagamentos) ===
    ASAAS_API_KEY: str | None = None
    ASAAS_BASE_URL: str = "https://sandbox.asaas.com/api/v3"
    ASAAS_WEBHOOK_TOKEN: str | None = None
    ASAAS_DUE_DAYS: int = 3

    # === PLANO PRO ===
    PRO_PLAN_PRICE: Decimal = Decimal("97.00")
    PRO_PLAN_DAYS: int = 30


settings = Settings()  # type: ignore[call-arg]
