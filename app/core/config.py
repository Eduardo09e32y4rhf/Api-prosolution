from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Prosolution IA"
    ENVIRONMENT: str = "local"
    
    SECRET_KEY: str
    TOKEN_EXPIRES_HOURS: int = 2
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./prosolution.db"
    
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    MERCADO_PAGO_ACCESS_TOKEN: str | None = None
    INSTAGRAM_ACCESS_TOKEN: str | None = None
    INSTAGRAM_APP_ID: str | None = None
    INSTAGRAM_APP_SECRET: str | None = None
    INSTAGRAM_REDIRECT_URI: str | None = None
    INSTAGRAM_BASE_URL: str = "https://graph.instagram.com"
    INSTAGRAM_API_VERSION: str = "v18.0"
    
    class Config:
        env_file = ".env"

settings = Settings()
