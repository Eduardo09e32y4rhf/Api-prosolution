from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0) # Seguro contra float
    status: Mapped[str] = mapped_column(String, default="pending") # approved, pending, cancelled
    external_id: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
