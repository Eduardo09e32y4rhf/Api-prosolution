from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database.base import Base

class InstagramPost(Base):
    __tablename__ = "instagram_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    instagram_id: Mapped[str] = mapped_column(String(50))
    image_url: Mapped[str] = mapped_column(Text)
    caption: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )