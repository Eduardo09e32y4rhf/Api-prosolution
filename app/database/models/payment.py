from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.timeutils import utcnow

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(String)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # Status do Asaas (PENDING, ...) ou os nossos: PAID | OVERDUE | REFUNDED | DELETED
    status: Mapped[str | None] = mapped_column(String, default="pending")
    external_id: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=utcnow)

    user: Mapped[User] = relationship(back_populates="payments")
