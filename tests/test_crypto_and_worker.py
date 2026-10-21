import asyncio
import os
from datetime import timedelta

import pytest
from sqlalchemy import select, text

from app import worker
from app.core.timeutils import utcnow
from app.database.models import BrandProfile, Post, User

from .conftest import Client


async def _user(db, email: str) -> User:
    return (await db.execute(select(User).where(User.email == email))).scalar_one()


async def test_instagram_token_is_encrypted_at_rest(client: Client, db):
    await client.register("ig@exemplo.com")
    user = await _user(db, "ig@exemplo.com")
    db.add(BrandProfile(user_id=user.id, ig_access_token="EAAsegredo", ig_account_id="1784"))
    await db.commit()

    raw = (await db.execute(text("SELECT ig_access_token FROM brand_profiles"))).scalar_one()
    assert "EAAsegredo" not in raw

    db.expire_all()
    brand = (await db.execute(select(BrandProfile))).scalar_one()
    assert brand.ig_access_token == "EAAsegredo"


async def test_instagram_callback_rejects_missing_or_wrong_state(client: Client):
    await client.register("ig@exemplo.com")
    resp = await client.get("/dashboard/instagram/callback?code=abc&state=forjado")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/dashboard/instagram?error=state"


async def test_instagram_connect_sets_state(client: Client, monkeypatch):
    await client.register("ig@exemplo.com")
    resp = await client.get("/dashboard/instagram/connect")
    assert resp.status_code == 307
    state = client.cookies.get("ig_oauth_state")
    assert state and f"state={state}" in resp.headers["location"]


async def test_worker_publishes_due_posts_once(client: Client, db, monkeypatch):
    await client.register("worker@exemplo.com")
    user = await _user(db, "worker@exemplo.com")
    db.add(BrandProfile(user_id=user.id, ig_access_token="EAAtoken", ig_account_id="1784"))
    due = Post(
        user_id=user.id,
        title="vencido",
        content="legenda",
        image_key="posts/1/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.jpg",
        status="scheduled",
        scheduled_for=utcnow() - timedelta(minutes=1),
    )
    future = Post(
        user_id=user.id,
        title="futuro",
        content="legenda",
        image_key="posts/1/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.jpg",
        status="scheduled",
        scheduled_for=utcnow() + timedelta(days=1),
    )
    no_image = Post(user_id=user.id, title="sem imagem", content="x", status="scheduled", scheduled_for=utcnow())
    db.add_all([due, future, no_image])
    await db.commit()

    due_id, future_id, no_image_id = due.id, future.id, no_image.id
    calls: list[dict] = []

    async def fake_publish(self, **kwargs):
        calls.append(kwargs)
        return "media_1"

    monkeypatch.setattr("app.instagram.service.InstagramService.publish_post", fake_publish)
    await worker.publish_scheduled_posts()
    await worker.publish_scheduled_posts()  # segunda rodada não publica de novo

    assert len(calls) == 1
    assert calls[0]["access_token"] == "EAAtoken"  # token descriptografado para a API
    db.expire_all()
    assert (await db.get(Post, due_id)).status == "published"
    assert (await db.get(Post, future_id)).status == "scheduled"
    assert (await db.get(Post, no_image_id)).status == "failed"


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="FOR UPDATE SKIP LOCKED só existe no Postgres",
)
async def test_concurrent_workers_never_claim_the_same_post(client: Client, db):
    await client.register("concorrencia@exemplo.com")
    user = await _user(db, "concorrencia@exemplo.com")
    db.add_all(
        Post(user_id=user.id, title=f"p{i}", content="x", status="scheduled", scheduled_for=utcnow())
        for i in range(120)
    )
    await db.commit()

    batches = await asyncio.gather(*(worker.claim_due_posts() for _ in range(4)))
    claimed = [post_id for batch in batches for post_id in batch]
    assert len(claimed) == len(set(claimed)), "um post foi pego por dois workers"
    assert len(claimed) == min(120, 4 * worker.BATCH_SIZE)
