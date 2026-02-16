from pydantic import BaseModel, EmailStr, Field


class PixPaymentSchema(BaseModel):
    email: EmailStr
    amount: float = Field(..., gt=0)
    description: str | None = None

