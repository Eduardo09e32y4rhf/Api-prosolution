from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.crypto import EncryptedString

from .base import Base

if TYPE_CHECKING:
    from .user import User


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    tone: Mapped[str | None] = mapped_column(String)
    style: Mapped[str | None] = mapped_column(String)
    emojis: Mapped[bool | None] = mapped_column(Boolean, default=True)
    forbidden_words: Mapped[str | None] = mapped_column(Text)
    cta: Mapped[str | None] = mapped_column(String)

    # Token de longa duração da Meta: criptografado em repouso
    ig_access_token: Mapped[str | None] = mapped_column(EncryptedString)
    ig_account_id: Mapped[str | None] = mapped_column(String)

    user: Mapped[User] = relationship(back_populates="brand_profile")
