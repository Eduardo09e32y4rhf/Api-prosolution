from app.core.rate_limit import limiter

from .conftest import PASSWORD, Client


async def test_post_without_csrf_token_is_rejected(client: Client):
    await client.get("/")  # recebe o cookie csrf, mas não manda o campo
    resp = await client.post("/auth/register", data={"email": "x@exemplo.com", "password": PASSWORD})
    assert resp.status_code == 403


async def test_post_with_wrong_csrf_token_is_rejected(client: Client):
    await client.fetch_csrf()
    resp = await client.post(
        "/auth/login", data={"email": "x@exemplo.com", "password": PASSWORD, "csrf_token": "outro-valor"}
    )
    assert resp.status_code == 403


async def test_dashboard_forms_require_csrf(client: Client):
    await client.register("csrf@exemplo.com")
    resp = await client.post("/dashboard/settings/business", data={"segment": "Padaria"})
    assert resp.status_code == 403


async def test_forms_render_csrf_field(client: Client):
    await client.register("forms@exemplo.com")
    for path in ("/dashboard/settings", "/dashboard/create", "/dashboard/subscription", "/dashboard/instagram"):
        resp = await client.get(path)
        assert resp.status_code == 200, path
        assert 'name="csrf_token"' in resp.text, path


async def test_login_is_rate_limited(client: Client):
    assert limiter.enabled
    statuses = [(await client.login("ninguem@exemplo.com", "errada")).status_code for _ in range(6)]
    assert statuses[:5] == [302] * 5
    assert statuses[5] == 429


async def test_recover_password_is_rate_limited(client: Client):
    statuses = [
        (await client.submit("/auth/recover-password", {"email": "a@exemplo.com"})).status_code for _ in range(4)
    ]
    assert statuses == [200, 200, 200, 429]
