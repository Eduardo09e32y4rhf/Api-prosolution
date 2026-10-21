from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.timeutils import utcnow

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Subscription(Base):
    """Assinatura do plano PRO. Cada pagamento confirmado estende `current_period_end`."""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    plan: Mapped[str] = mapped_column(String, default="pro")
    # active | canceled
    status: Mapped[str] = mapped_column(String, default="active")
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="subscription")

    @property
    def is_active(self) -> bool:
        return self.status == "active" and self.current_period_end is not None and self.current_period_end > utcnow()
