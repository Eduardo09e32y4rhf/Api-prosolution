from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from payments.schemas import PixPaymentSchema
from payments.service import create_pix_payment

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/pix")
async def create_pix_payment_route(
    data: PixPaymentSchema,
    db: AsyncSession = Depends(get_db),
):
    return await create_pix_payment(
        db,
        amount=data.amount,
        description=data.description,
        email=data.email,
    )
