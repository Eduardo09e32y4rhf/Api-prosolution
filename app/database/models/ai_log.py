from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .base import Base

class AILog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
