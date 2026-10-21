from sqlalchemy import select

from app.database.models import Post, User

from .conftest import Client


async def _create_post(db, email: str, title: str) -> Post:
    user = (await db.execute(select(User).where(User.email == email))).scalar_one()
    post = Post(user_id=user.id, title=title, content=f"conteúdo de {title}")
    db.add(post)
    await db.commit()
    return post


async def test_user_cannot_see_other_users_posts(client: Client, other_client: Client, db):
    await client.register("alice@exemplo.com")
    await other_client.register("bob@exemplo.com")
    await _create_post(db, "alice@exemplo.com", "Post secreto da Alice")

    alice_page = await client.get("/dashboard/create")
    bob_page = await other_client.get("/dashboard/create")
    assert "Post secreto da Alice" in alice_page.text
    assert "Post secreto da Alice" not in bob_page.text


async def test_user_cannot_delete_or_schedule_other_users_post(client: Client, other_client: Client, db):
    await client.register("alice@exemplo.com")
    await other_client.register("bob@exemplo.com")
    post = await _create_post(db, "alice@exemplo.com", "Post da Alice")

    delete = await other_client.submit(f"/dashboard/posts/{post.id}/delete")
    assert delete.status_code == 404
    schedule = await other_client.submit(f"/dashboard/posts/{post.id}/schedule", {"scheduled_for": "2030-01-01T10:00"})
    assert schedule.status_code == 404

    await db.refresh(post)
    assert post.status == "draft"


async def test_schedule_converts_local_time_to_utc(client: Client, db):
    await client.register("alice@exemplo.com")
    post = await _create_post(db, "alice@exemplo.com", "Agendado")

    resp = await client.submit(
        f"/dashboard/posts/{post.id}/schedule",
        {"scheduled_for": "2030-01-01T10:00", "image_url": "https://exemplo.com/img.jpg"},
    )
    assert resp.status_code == 302
    await db.refresh(post)
    assert post.status == "scheduled"
    # America/Sao_Paulo é UTC-3
    assert post.scheduled_for is not None and post.scheduled_for.isoformat() == "2030-01-01T13:00:00"
    assert post.image_url == "https://exemplo.com/img.jpg"

    calendar = await client.get("/dashboard/calendar")
    assert "2030-01-01T10:00:00" in calendar.text


async def test_calendar_escapes_post_content(client: Client, db):
    await client.register("alice@exemplo.com")
    user = (await db.execute(select(User).where(User.email == "alice@exemplo.com"))).scalar_one()
    from datetime import datetime

    db.add(
        Post(
            user_id=user.id,
            title="x",
            content="</script><script>alert(1)</script>`${alert(2)}`",
            status="scheduled",
            scheduled_for=datetime(2030, 1, 1, 13, 0),
        )
    )
    await db.commit()

    page = await client.get("/dashboard/calendar")
    assert "<script>alert(1)" not in page.text
    assert "</script><script>" not in page.text


async def test_settings_are_saved_per_user(client: Client, other_client: Client):
    await client.register("alice@exemplo.com")
    await other_client.register("bob@exemplo.com")

    await client.submit("/dashboard/settings/business", {"segment": "Padaria da Alice"})
    assert "Padaria da Alice" in (await client.get("/dashboard/settings")).text
    assert "Padaria da Alice" not in (await other_client.get("/dashboard/settings")).text
