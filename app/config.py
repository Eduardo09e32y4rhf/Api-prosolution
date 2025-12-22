from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Carrega variáveis do .env
load_dotenv()


class Settings(BaseSettings):
    # === Banco de dados ===
    DATABASE_URL: str
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    ENV: str = "development"

    # === Configurações do Instagram ===
    INSTAGRAM_ACCESS_TOKEN: str
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str
    INSTAGRAM_API_VERSION: str = "v24.0"
    INSTAGRAM_BASE_URL: str = "https://graph.facebook.com"

    # === Configurações do Gemini ===
    GEMINI_API_KEY: str

    class Config:
        env_file = ".env"
        extra = "allow"  # Permite variáveis extras sem erro


# Instância global para importar em outros módulos
settings = Settings()


# Variáveis de acesso rápido (sem precisar chamar settings.xxx)
INSTAGRAM_ACCESS_TOKEN = settings.INSTAGRAM_ACCESS_TOKEN
INSTAGRAM_BUSINESS_ACCOUNT_ID = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID
INSTAGRAM_API_VERSION = settings.INSTAGRAM_API_VERSION
INSTAGRAM_BASE_URL = settings.INSTAGRAM_BASE_URL
GEMINI_API_KEY = settings.GEMINI_API_KEY
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
