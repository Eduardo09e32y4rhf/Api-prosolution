from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # === APP ===
    APP_NAME: str = "Prosolution IA"
    ENV: str = "development"

    # === DATABASE ===
    DATABASE_URL: str = "sqlite+aiosqlite:///./prosolution.db"

    # === OPENAI ===
    OPENAI_API_KEY: str | None = None

    # === GEMINI ===
    GEMINI_API_KEY: str | None = None

    # === INSTAGRAM ===
    INSTAGRAM_BASE_URL: str = "https://graph.facebook.com"
    INSTAGRAM_API_VERSION: str = "v24.0"
    INSTAGRAM_ACCESS_TOKEN: str | None = None
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str | None = None

    # === MERCADO PAGO ===
    MERCADO_PAGO_ACCESS_TOKEN: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
