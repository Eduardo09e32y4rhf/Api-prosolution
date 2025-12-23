import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "app" / "database" / "models"

MODELS_DIR.mkdir(parents=True, exist_ok=True)

files = {
    "base.py": """from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
""",

    "user.py": """from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
""",

    "post.py": """from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .base import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    platform = Column(String, default="instagram")
    created_at = Column(DateTime, default=datetime.utcnow)
""",

    "payment.py": """from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .base import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
""",

    "ai_log.py": """from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .base import Base

class AILog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
""",

    "__init__.py": """from .base import Base
from .user import User
from .post import Post
from .payment import Payment
from .ai_log import AILog

__all__ = [
    "Base",
    "User",
    "Post",
    "Payment",
    "AILog",
]
"""
}

for filename, content in files.items():
    path = MODELS_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✔ criado/atualizado: {path}")

print("\\n✅ MODELS CRIADOS COM SUCESSO")
print("👉 Agora rode: py -m uvicorn app.main:app --reload")
