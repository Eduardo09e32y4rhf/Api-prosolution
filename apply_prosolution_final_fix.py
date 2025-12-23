# apply_prosolution_final_fix.py
# Script FINAL para corrigir estrutura, imports, settings e base do Prosolution IA

from pathlib import Path

BASE_DIR = Path(__file__).parent

files = {
    "app/database/models/__init__.py": """\
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
""",

    "app/database/base.py": """\
from app.database.models import Base
from app.database.session import engine

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
""",

    "app/config.py": """\
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
""",

    "app/payments/schemas.py": """\
from pydantic import BaseModel, EmailStr, Field

class PixPaymentSchema(BaseModel):
    email: EmailStr
    amount: float = Field(..., gt=0)
""",

    "requirements.txt": """\
fastapi==0.124.4
uvicorn==0.38.0

SQLAlchemy==2.0.36
greenlet>=3.0.0
aiosqlite
asyncpg

python-dotenv==1.2.1
pydantic-settings
email-validator

requests
jinja2
"""
}

for relative_path, content in files.items():
    path = BASE_DIR / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✔ corrigido: {relative_path}")

print("\\n✅ FIX FINAL APLICADO COM SUCESSO")
