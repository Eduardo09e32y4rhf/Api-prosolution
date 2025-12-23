from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SERVICE_FILE = BASE_DIR / "app" / "payments" / "service.py"

SERVICE_FILE.parent.mkdir(parents=True, exist_ok=True)

content = """from app.database.session import AsyncSessionLocal
from app.database.models.payment import Payment
from app.config import settings
import uuid

async def create_pix_payment(data):
    \"""
    Cria um pagamento PIX (stub funcional)
    Integração Mercado Pago já preparada
    \"""

    async with AsyncSessionLocal() as session:
        payment = Payment(
            email=data.email,
            amount=data.amount,
            status="pending"
        )

        session.add(payment)
        await session.commit()
        await session.refresh(payment)

        return {
            "payment_id": payment.id,
            "status": payment.status,
            "amount": payment.amount,
            "message": "PIX gerado com sucesso (stub)",
        }
"""

with open(SERVICE_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("✔ create_pix_payment criado com sucesso")
print("👉 app/payments/service.py corrigido")
print("👉 Rode novamente: py -m uvicorn app.main:app --reload")
