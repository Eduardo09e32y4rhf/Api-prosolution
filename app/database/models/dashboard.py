from sqlalchemy import Column, Integer, String, DateTime, Numeric
from sqlalchemy.sql import func
from app.database.base import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    instagram_id = Column(String, unique=True)
    caption = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    mp_payment_id = Column(String, unique=True)
    status = Column(String)
    amount = Column(Numeric)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AILog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True)
    action = Column(String)
    provider = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
