import os
from pathlib import Path

ROOT = Path.cwd()

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✔ atualizado: {path}")

# ======================================================
# 1️⃣ .env.example (SEGURANÇA)
# ======================================================
write(ROOT / ".env.example", """
# INSTAGRAM
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_BUSINESS_ACCOUNT_ID=
INSTAGRAM_API_VERSION=v24.0
INSTAGRAM_BASE_URL=https://graph.facebook.com

# IA
GEMINI_API_KEY=
OPENAI_API_KEY=

# DATABASE
DATABASE_URL=postgresql+asyncpg://user:password@localhost/prosolution
""")

# ======================================================
# 2️⃣ BANCO DE DADOS — UNIFICADO (ASYNC POSTGRES)
# ======================================================
write(ROOT / "app/database/session.py", """
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
""")

write(ROOT / "app/database/base.py", """
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
""")

# ======================================================
# 3️⃣ AUTH ÚNICA (REMOVE AUTH FAKE)
# ======================================================
write(ROOT / "app/auth/routes.py", """
from fastapi import APIRouter, Depends
from app.auth.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/me")
async def me(user=Depends(get_current_user)):
    return user
""")

# ======================================================
# 4️⃣ IA — PADRONIZAÇÃO PROVIDERS
# ======================================================
write(ROOT / "app/ai/providers/base.py", """
from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass
""")

write(ROOT / "app/ai/providers/gemini.py", """
import google.generativeai as genai
from app.config import settings
from app.ai.providers.base import AIProvider

genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiProvider(AIProvider):
    def generate(self, prompt: str) -> str:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text
""")

write(ROOT / "app/ai/providers/openai.py", """
from openai import OpenAI
from app.config import settings
from app.ai.providers.base import AIProvider

class OpenAIProvider(AIProvider):
    def generate(self, prompt: str) -> str:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content
""")

# ======================================================
# 5️⃣ ORQUESTRADOR IA (ÚNICO)
# ======================================================
write(ROOT / "app/ai/orchestrator.py", """
from app.ai.providers.gemini import GeminiProvider

def generate_instagram_content(prompt: str) -> str:
    provider = GeminiProvider()
    return provider.generate(prompt)
""")

# ======================================================
# 6️⃣ SCHEDULER CORRIGIDO
# ======================================================
write(ROOT / "app/scheduler/scheduler.py", """
from app.ai.orchestrator import generate_instagram_content

def run():
    content = generate_instagram_content("Post institucional")
    print(content)
""")

# ======================================================
# 7️⃣ CONFIG CENTRALIZADA
# ======================================================
write(ROOT / "app/config.py", """
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
""")

print("\\n✅ TODAS AS CORREÇÕES FORAM APLICADAS COM SUCESSO")
