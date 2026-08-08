from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    segment = Column(String, nullable=True)
    products = Column(Text, nullable=True)
    services = Column(Text, nullable=True)
    audience = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    whatsapp = Column(String, nullable=True)
    objective = Column(String, nullable=True)

    user = relationship("User", back_populates="business")
