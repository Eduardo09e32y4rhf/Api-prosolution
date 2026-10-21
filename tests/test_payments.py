from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core.timeutils import utcnow
from app.database.models import Payment, Subscription, User

from .conftest import Client

WEBHOOK = "/api/asaas/webhook"
TOKEN_HEADER = {"asaas-access-token": "webhook-test-token"}


@pytest.fixture
async def customer(client: Client, db) -> SimpleNamespace:
    """Usuário com cliente no Asaas e uma cobrança pendente gerada pela aplicação."""
    await client.register("cliente@exemplo.com")
    user = (await db.execute(select(User).where(User.email == "cliente@exemplo.com"))).scalar_one()
    user.asaas_customer_id = "cus_123"
    db.add(Payment(user_id=user.id, email=user.email, amount=Decimal("97.00"), status="PENDING", external_id="pay_1"))
    await db.commit()
    # Só os valores: os testes chamam expire_all() e um objeto ORM expirado não pode recarregar fora de await
    return SimpleNamespace(id=user.id, email=user.email)


def event(name: str, payment_id: str = "pay_1", customer_id: str = "cus_123") -> dict:
    return {"event": name, "payment": {"id": payment_id, "customer": customer_id}}


async def _subscription(db, user: SimpleNamespace) -> Subscription | None:
    db.expire_all()
    return (await db.execute(select(Subscription).where(Subscription.user_id == user.id))).scalar_one_or_none()


async def test_webhook_without_token_is_rejected(client: Client, customer: SimpleNamespace, db):
    resp = await client.post(WEBHOOK, json=event("PAYMENT_CONFIRMED"))
    assert resp.status_code == 401
    assert await _subscription(db, customer) is None


async def test_webhook_with_wrong_token_is_rejected(client: Client, customer: SimpleNamespace, db):
    resp = await client.post(WEBHOOK, json=event("PAYMENT_CONFIRMED"), headers={"asaas-access-token": "errado"})
    assert resp.status_code == 401
    assert await _subscription(db, customer) is None


async def test_webhook_rejects_everything_when_token_not_configured(
    client: Client, customer: SimpleNamespace, monkeypatch
):
    monkeypatch.setattr("app.payments.webhooks.settings.ASAAS_WEBHOOK_TOKEN", None)
    resp = await client.post(WEBHOOK, json=event("PAYMENT_CONFIRMED"), headers=TOKEN_HEADER)
    assert resp.status_code == 503


async def test_confirmed_payment_activates_subscription_for_30_days(client: Client, customer: SimpleNamespace, db):
    resp = await client.post(WEBHOOK, json=event("PAYMENT_CONFIRMED"), headers=TOKEN_HEADER)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Subscription extended"

    sub = await _subscription(db, customer)
    assert sub is not None and sub.is_active
    assert sub.current_period_end is not None
    assert timedelta(days=29, hours=23) < sub.current_period_end - utcnow() <= timedelta(days=30)

    page = await client.get("/dashboard/subscription")
    assert "Ativo até" in page.text


async def test_duplicate_events_do_not_extend_twice(client: Client, customer: SimpleNamespace, db):
    await client.post(WEBHOOK, json=event("PAYMENT_CONFIRMED"), headers=TOKEN_HEADER)
    first_end = (await _subscription(db, customer)).current_period_end

    resp = await client.post(WEBHOOK, json=event("PAYMENT_RECEIVED"), headers=TOKEN_HEADER)
    assert resp.json()["message"] == "Already processed"
    assert (await _subscription(db, customer)).current_period_end == first_end


async def test_renewal_adds_to_remaining_period(client: Client, customer: SimpleNamespace, db):
    await client.post(WEBHOOK, json=event("PAYMENT_CONFIRMED"), headers=TOKEN_HEADER)
    first_end = (await _subscription(db, customer)).current_period_end

    db.add(
        Payment(
            user_id=customer.id, email=customer.email, amount=Decimal("97.00"), status="PENDING", external_id="pay_2"
        )
    )
    await db.commit()
    await client.post(WEBHOOK, json=event("PAYMENT_CONFIRMED", payment_id="pay_2"), headers=TOKEN_HEADER)

    assert (await _subscription(db, customer)).current_period_end == first_end + timedelta(days=30)


async def test_unknown_payment_is_ignored(client: Client, customer: SimpleNamespace, db):
    """Um pagamento que não foi gerado pela aplicação não libera o plano."""
    resp = await client.post(WEBHOOK, json=event("PAYMENT_CONFIRMED", payment_id="pay_forjado"), headers=TOKEN_HEADER)
    assert resp.json() == {"status": "ignored", "reason": "Payment not found"}
    assert await _subscription(db, customer) is None


async def test_refund_revokes_subscription(client: Client, customer: SimpleNamespace, db):
    await client.post(WEBHOOK, json=event("PAYMENT_CONFIRMED"), headers=TOKEN_HEADER)
    await client.post(WEBHOOK, json=event("PAYMENT_REFUNDED"), headers=TOKEN_HEADER)

    sub = await _subscription(db, customer)
    assert sub is not None and not sub.is_active
    assert sub.status == "canceled"


async def test_overdue_does_not_revoke_paid_period(client: Client, customer: SimpleNamespace, db):
    await client.post(WEBHOOK, json=event("PAYMENT_CONFIRMED"), headers=TOKEN_HEADER)
    db.add(
        Payment(
            user_id=customer.id, email=customer.email, amount=Decimal("97.00"), status="PENDING", external_id="pay_2"
        )
    )
    await db.commit()
    await client.post(WEBHOOK, json=event("PAYMENT_OVERDUE", payment_id="pay_2"), headers=TOKEN_HEADER)

    assert (await _subscription(db, customer)).is_active


async def test_subscription_expires_after_period_end(client: Client, customer: SimpleNamespace, db):
    await client.post(WEBHOOK, json=event("PAYMENT_CONFIRMED"), headers=TOKEN_HEADER)
    sub = await _subscription(db, customer)
    sub.current_period_end = utcnow() - timedelta(minutes=1)
    await db.commit()

    assert not sub.is_active
    page = await client.get("/dashboard/subscription")
    assert "Ativo até" not in page.text
    assert "Assinar PRO" in page.text


async def test_upgrade_creates_local_payment_and_redirects_to_invoice(
    client: Client, customer: SimpleNamespace, db, monkeypatch
):
    async def fake_payment_link(self, customer_id, value, description):
        assert customer_id == "cus_123"
        return {"payment_id": "pay_novo", "invoice_url": "https://sandbox.asaas.com/i/pay_novo", "status": "PENDING"}

    monkeypatch.setattr("app.payments.asaas.AsaasService.create_payment_link", fake_payment_link)
    resp = await client.submit("/dashboard/subscription/upgrade")
    assert resp.status_code == 302
    assert resp.headers["location"] == "https://sandbox.asaas.com/i/pay_novo"

    payment = (await db.execute(select(Payment).where(Payment.external_id == "pay_novo"))).scalar_one()
    assert payment.user_id == customer.id and payment.amount == Decimal("97.00")
