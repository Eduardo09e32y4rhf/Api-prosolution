from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    tone = Column(String, nullable=True)
    style = Column(String, nullable=True)
    emojis = Column(Boolean, default=True)
    forbidden_words = Column(Text, nullable=True)
    cta = Column(String, nullable=True)
    
    ig_access_token = Column(String, nullable=True)
    ig_account_id = Column(String, nullable=True)

    user = relationship("User", back_populates="brand_profile")
