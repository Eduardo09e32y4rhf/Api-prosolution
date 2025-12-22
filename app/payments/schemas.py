from pydantic import BaseModel, EmailStr, Field


class PixPaymentSchema(BaseModel):
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=3)
    email: EmailStr