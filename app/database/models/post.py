from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .base import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    platform = Column(String, default="instagram")
    created_at = Column(DateTime, default=datetime.utcnow)
