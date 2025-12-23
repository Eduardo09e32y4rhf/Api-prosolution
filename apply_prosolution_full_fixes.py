from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✔ atualizado: {path}")

# ==================================================
# BASE SQLALCHEMY
# ==================================================
write(
    BASE_DIR / "app/database/models/base.py",
    """
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
"""
)

# ==================================================
# AI LOG MODEL (CORREÇÃO DO ERRO)
# ==================================================
write(
    BASE_DIR / "app/database/models/ai_log.py",
    """
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database.models.base import Base

class AILog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True)
    action = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
"""
)

# ==================================================
# INIT MODELS
# ==================================================
write(
    BASE_DIR / "app/database/models/__init__.py",
    """
from .base import Base
from .ai_log import AILog
"""
)

# ==================================================
# SYSTEM ADMIN (BLINDADO)
# ==================================================
write(
    BASE_DIR / "app/ai/admin/system_admin.py",
    """
from datetime import datetime
from app.database.session import AsyncSessionLocal
from app.database.models.ai_log import AILog

async def evaluate_system():
    return {
        "status": "ok",
        "checked_at": datetime.utcnow().isoformat()
    }

async def log_ai_action(action: str):
    async with AsyncSessionLocal() as session:
        log = AILog(action=action)
        session.add(log)
        await session.commit()
"""
)

print("\\n✅ CORREÇÃO FINAL APLICADA (AI LOG + BASE)")
