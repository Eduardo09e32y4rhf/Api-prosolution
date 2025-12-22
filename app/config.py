
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""
    INSTAGRAM_API_VERSION: str = "v24.0"
    INSTAGRAM_BASE_URL: str = "https://graph.facebook.com"

    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    DATABASE_URL: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
