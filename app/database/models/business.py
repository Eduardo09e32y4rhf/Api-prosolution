from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    segment: Mapped[str | None] = mapped_column(String)
    products: Mapped[str | None] = mapped_column(Text)
    services: Mapped[str | None] = mapped_column(Text)
    audience: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String)
    whatsapp: Mapped[str | None] = mapped_column(String)
    objective: Mapped[str | None] = mapped_column(String)

    user: Mapped[User] = relationship(back_populates="business")
