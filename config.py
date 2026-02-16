from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Prosolution IA"
    ENV: str = "development"

    # SECURITY
    SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET"
    TOKEN_EXPIRES_HOURS: int = 2

    # DATABASE (ASYNC ONLY)
    DATABASE_URL: str = "sqlite+aiosqlite:///./prosolution.db"

    # MERCADO PAGO
    MERCADO_PAGO_ACCESS_TOKEN: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
