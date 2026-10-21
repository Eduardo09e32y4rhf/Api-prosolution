from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.timeutils import utcnow

from .base import Base

if TYPE_CHECKING:
    from .ai_log import AILog
    from .brand_profile import BrandProfile
    from .business import Business
    from .payment import Payment
    from .post import Post
    from .subscription import Subscription


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=utcnow)
    asaas_customer_id: Mapped[str | None] = mapped_column(String)

    business: Mapped[Business | None] = relationship(back_populates="user", cascade="all, delete-orphan")
    brand_profile: Mapped[BrandProfile | None] = relationship(back_populates="user", cascade="all, delete-orphan")
    subscription: Mapped[Subscription | None] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    posts: Mapped[list[Post]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[list[Payment]] = relationship(back_populates="user", cascade="all, delete-orphan")
    ai_logs: Mapped[list[AILog]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def display_name(self) -> str:
        return self.email.split("@")[0].capitalize()

    @property
    def is_vip(self) -> bool:
        return self.subscription is not None and self.subscription.is_active
