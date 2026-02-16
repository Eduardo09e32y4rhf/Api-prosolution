from pydantic import BaseModel, EmailStr, Field


class PixPaymentSchema(BaseModel):
    email: EmailStr
    amount: float = Field(..., gt=0)
    description: str = Field(default="Pagamento PIX Prosolution IA", min_length=3, max_length=255)
