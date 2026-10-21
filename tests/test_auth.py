from jose import jwt
from sqlalchemy import select

from app.core.config import settings
from app.database.models import User
from app.security import create_password_reset_token, verify_password

from .conftest import PASSWORD, Client


async def test_register_creates_user_and_logs_in(client: Client, db):
    resp = await client.register("Novo@Exemplo.com ")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/dashboard"
    assert "token" in client.cookies

    user = (await db.execute(select(User).where(User.email == "novo@exemplo.com"))).scalar_one()
    assert user.password_hash != PASSWORD
    assert verify_password(PASSWORD, user.password_hash)

    dashboard = await client.get("/dashboard/")
    assert dashboard.status_code == 200
    assert "Novo" in dashboard.text


async def test_register_rejects_duplicate_email(client: Client, other_client: Client):
    await client.register("dup@exemplo.com")
    resp = await other_client.register("dup@exemplo.com")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/?error=email_taken"


async def test_register_rejects_short_password(client: Client):
    resp = await client.register("curta@exemplo.com", password="123")
    assert resp.headers["location"] == "/?error=weak_password"


async def test_login_success_and_wrong_password(client: Client, other_client: Client):
    await client.register("login@exemplo.com")

    wrong = await other_client.login("login@exemplo.com", "senha-errada")
    assert wrong.headers["location"] == "/?error=invalid_credentials"
    assert "token" not in other_client.cookies

    ok = await other_client.login("login@exemplo.com")
    assert ok.status_code == 302
    assert ok.headers["location"] == "/dashboard"
    assert (await other_client.get("/dashboard/")).status_code == 200


async def test_dashboard_requires_login(client: Client):
    resp = await client.get("/dashboard/")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/"


async def test_logout_clears_session(client: Client):
    await client.register("logout@exemplo.com")
    resp = await client.submit("/auth/logout")
    assert resp.headers["location"] == "/"
    assert (await client.get("/dashboard/")).status_code == 302


async def test_users_list_endpoint_was_removed(client: Client):
    assert (await client.get("/api/users")).status_code == 404


async def test_recover_password_does_not_leak_token(client: Client, monkeypatch):
    sent: list[tuple[str, str, str]] = []

    async def fake_send(to: str, subject: str, body: str) -> None:
        sent.append((to, subject, body))

    monkeypatch.setattr("app.auth.routes.send_email", fake_send)
    await client.register("reset@exemplo.com")

    resp = await client.submit("/auth/recover-password", {"email": "reset@exemplo.com"})
    assert resp.status_code == 200
    assert "token=" not in resp.text
    assert "eyJ" not in resp.text  # nenhum JWT na resposta
    assert len(sent) == 1 and sent[0][0] == "reset@exemplo.com"
    assert "https://testserver/auth/reset-password?token=" in sent[0][2]

    # Mesma resposta para e-mail inexistente (sem enumeração) e nenhum e-mail enviado
    unknown = await client.submit("/auth/recover-password", {"email": "ninguem@exemplo.com"})
    assert unknown.status_code == 200
    assert len(sent) == 1


async def test_reset_password_flow_and_token_is_single_use(client: Client, other_client: Client, db):
    await client.register("troca@exemplo.com")
    user = (await db.execute(select(User).where(User.email == "troca@exemplo.com"))).scalar_one()
    token = create_password_reset_token(user)

    await other_client.fetch_csrf(f"/auth/reset-password?token={token}")
    resp = await other_client.submit("/auth/reset-password", {"token": token, "new_password": "nova-senha-456"})
    assert resp.status_code == 302
    assert resp.headers["location"] == "/?msg=password_reset"

    assert (await other_client.login("troca@exemplo.com", "nova-senha-456")).headers["location"] == "/dashboard"

    # O mesmo link não funciona de novo depois que a senha mudou
    again = await other_client.submit("/auth/reset-password", {"token": token, "new_password": "outra-senha-789"})
    assert again.status_code == 400


async def test_reset_token_cannot_be_used_as_session(client: Client, db):
    await client.register("sessao@exemplo.com")
    user = (await db.execute(select(User).where(User.email == "sessao@exemplo.com"))).scalar_one()
    client.cookies.delete("token")
    client.cookies.set("token", create_password_reset_token(user))
    assert (await client.get("/dashboard/")).status_code == 302


async def test_forged_session_token_is_rejected(client: Client):
    await client.register("forjado@exemplo.com")
    forged = jwt.encode({"sub": "forjado@exemplo.com", "type": "session"}, "chave-errada", algorithm="HS256")
    client.cookies.delete("token")
    client.cookies.set("token", forged)
    assert (await client.get("/dashboard/")).status_code == 302
    assert settings.SECRET_KEY != "chave-errada"
