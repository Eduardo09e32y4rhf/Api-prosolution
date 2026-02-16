from fastapi import APIRouter
from app.payments.schemas import PixPaymentSchema
from app.payments.service import create_pix_payment

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/pix")
async def create_pix_payment_route(data: PixPaymentSchema):
    return await create_pix_payment(
        amount=data.amount,
        description=data.description,
        email=data.email,
    )