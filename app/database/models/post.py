from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    image_url: Mapped[str | None] = mapped_column(String)
    platform: Mapped[str | None] = mapped_column(String, default="instagram")
    # draft | scheduled | publishing | published | failed
    status: Mapped[str | None] = mapped_column(String, default="draft")
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime)  # UTC
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=utcnow)

    user: Mapped[User] = relationship(back_populates="posts")
