from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.storage import storage
from app.core.timeutils import utcnow

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    # Chave da imagem no armazenamento (posts/<user>/<uuid>.jpg); a URL pública é derivada
    image_key: Mapped[str | None] = mapped_column(String)
    platform: Mapped[str | None] = mapped_column(String, default="instagram")
    # draft | scheduled | publishing | published | failed
    status: Mapped[str | None] = mapped_column(String, default="draft")
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime)  # UTC
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=utcnow)

    user: Mapped[User] = relationship(back_populates="posts")

    @property
    def image_url(self) -> str | None:
        return storage.public_url(self.image_key) if self.image_key else None
