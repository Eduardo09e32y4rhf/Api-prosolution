"""Semana 2: edição de legenda, upload de imagem, agendamento e limites."""

import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import worker
from app.core.config import settings
from app.core.storage import LocalStorage, storage
from app.core.timeutils import utcnow
from app.database.models import BrandProfile, Post, User

from .conftest import Client
from .imgs import make_image, open_image

assert isinstance(storage, LocalStorage)
MEDIA_ROOT = storage.root


def media_files() -> list[str]:
    return sorted(str(p.relative_to(MEDIA_ROOT)) for p in MEDIA_ROOT.rglob("*.jpg"))


def local_time_in(**delta) -> str:
    """Horário local (fuso da aplicação) no formato do <input type=datetime-local>."""
    return (datetime.now(ZoneInfo(settings.APP_TIMEZONE)) + timedelta(**delta)).strftime("%Y-%m-%dT%H:%M")


async def make_post(db: AsyncSession, email: str, **fields) -> int:
    user = (await db.execute(select(User).where(User.email == email))).scalar_one()
    post = Post(
        user_id=user.id,
        title=fields.pop("title", "Post de teste"),
        content=fields.pop("content", "Legenda de teste"),
        **fields,
    )
    db.add(post)
    await db.commit()
    return post.id


async def fresh(db: AsyncSession, post_id: int) -> Post:
    db.expire_all()
    return (await db.execute(select(Post).where(Post.id == post_id))).scalar_one()


@pytest.fixture(autouse=True)
def _clean_media():
    for f in MEDIA_ROOT.rglob("*.jpg"):
        f.unlink()
    yield


@pytest.fixture
async def alice(client: Client, db: AsyncSession) -> tuple[Client, int]:
    await client.register("alice@exemplo.com")
    return client, await make_post(db, "alice@exemplo.com")


# ---------- upload ----------


async def test_upload_stores_processed_image_and_serves_it(alice, db):
    client, post_id = alice
    resp = await client.upload(
        f"/dashboard/posts/{post_id}/image", make_image(2000, 2000, "PNG"), "foto.png", "image/png"
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == f"/dashboard/posts/{post_id}/edit?msg=image_saved"

    post = await fresh(db, post_id)
    assert post.image_key and post.image_key.startswith("posts/")
    assert media_files() == [post.image_key]

    served = await client.get(post.image_url.removeprefix("https://testserver"))
    assert served.status_code == 200
    assert served.headers["content-type"] == "image/jpeg"
    image = open_image(served.content)
    assert image.format == "JPEG" and image.width == 1440  # PNG 2000px reduzido e convertido

    page = await client.get(f"/dashboard/posts/{post_id}/edit")
    assert post.image_url in page.text


async def test_upload_reports_when_the_image_was_cropped(alice):
    client, post_id = alice
    resp = await client.upload(f"/dashboard/posts/{post_id}/image", make_image(3000, 600))
    assert resp.headers["location"].endswith("msg=image_cropped")
    page = await client.get(resp.headers["location"])
    assert "Ajustamos o enquadramento" in page.text


async def test_replacing_image_deletes_the_previous_file(alice, db):
    client, post_id = alice
    await client.upload(f"/dashboard/posts/{post_id}/image", make_image(800, 800))
    first = (await fresh(db, post_id)).image_key
    await client.upload(f"/dashboard/posts/{post_id}/image", make_image(900, 900))
    second = (await fresh(db, post_id)).image_key

    assert first != second
    assert media_files() == [second], "a imagem antiga não pode ficar órfã no armazenamento"


@pytest.mark.parametrize(
    ("content", "filename", "mime", "expected"),
    [
        (b"isto e texto puro", "foto.jpg", "image/jpeg", "Não foi possível ler a imagem"),
        (b"<svg xmlns='http://www.w3.org/2000/svg'/>", "x.png", "image/png", "Não foi possível ler a imagem"),
        (make_image(800, 800, "GIF"), "a.gif", "image/gif", "Formato não suportado"),
        (make_image(200, 200), "pequena.jpg", "image/jpeg", "pequena demais"),
        (b"", "vazio.jpg", "image/jpeg", "vazio"),
    ],
    ids=["texto-com-extensao-jpg", "svg", "gif", "pequena", "vazio"],
)
async def test_invalid_uploads_show_friendly_error_and_change_nothing(alice, db, content, filename, mime, expected):
    client, post_id = alice
    resp = await client.upload(f"/dashboard/posts/{post_id}/image", content, filename, mime)
    assert resp.status_code == 400
    assert expected in resp.text
    assert (await fresh(db, post_id)).image_key is None
    assert media_files() == []


async def test_upload_requires_csrf_token(alice):
    client, post_id = alice
    resp = await client.upload(f"/dashboard/posts/{post_id}/image", make_image(800, 800), send_csrf=False)
    assert resp.status_code == 403
    assert media_files() == []


async def test_oversized_upload_is_rejected_with_413_before_being_processed(alice, db):
    client, post_id = alice
    huge = make_image(800, 800) + b"\0" * (11 * 1024 * 1024)  # acima do limite de 10 MB da requisição
    resp = await client.upload(f"/dashboard/posts/{post_id}/image", huge)
    assert resp.status_code == 413
    assert media_files() == [] and (await fresh(db, post_id)).image_key is None


async def test_chunked_upload_without_content_length_is_also_limited(alice):
    client, post_id = alice
    boundary = "xyzboundary"

    async def body():
        yield (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="a.jpg"\r\n'
            "Content-Type: image/jpeg\r\n\r\n"
        ).encode()
        for _ in range(14):  # 14 MB enviados aos poucos, sem Content-Length
            yield b"\0" * (1024 * 1024)

    resp = await client.post(
        f"/dashboard/posts/{post_id}/image",
        content=body(),
        headers={"content-type": f"multipart/form-data; boundary={boundary}"},
    )
    assert resp.status_code == 413
    assert media_files() == []


async def test_database_failure_does_not_leave_orphan_file(alice, monkeypatch):
    client, post_id = alice
    with monkeypatch.context() as m:

        async def broken_commit(self):
            raise RuntimeError("banco caiu")

        m.setattr(AsyncSession, "commit", broken_commit)
        with pytest.raises(RuntimeError, match="banco caiu"):
            await client.upload(f"/dashboard/posts/{post_id}/image", make_image(800, 800))
    assert media_files() == []


async def test_storage_failure_leaves_post_untouched(alice, db, monkeypatch):
    client, post_id = alice

    async def broken_save(self, key, data):
        raise OSError("disco cheio")

    monkeypatch.setattr(LocalStorage, "save", broken_save)
    with pytest.raises(OSError, match="disco cheio"):
        await client.upload(f"/dashboard/posts/{post_id}/image", make_image(800, 800))
    assert (await fresh(db, post_id)).image_key is None


# ---------- isolamento entre usuários ----------


async def test_other_users_cannot_touch_the_post(alice, other_client: Client, db):
    client, post_id = alice
    await client.upload(f"/dashboard/posts/{post_id}/image", make_image(800, 800))
    await other_client.register("bob@exemplo.com")
    files_before = media_files()

    base = f"/dashboard/posts/{post_id}"
    assert (await other_client.get(f"{base}/edit")).status_code == 404
    assert (await other_client.submit(f"{base}/edit", {"title": "hack", "content": "hack"})).status_code == 404
    assert (await other_client.upload(f"{base}/image", make_image(800, 800))).status_code == 404
    assert (await other_client.submit(f"{base}/image/remove")).status_code == 404
    assert (await other_client.submit(f"{base}/schedule", {"scheduled_for": local_time_in(days=1)})).status_code == 404
    assert (await other_client.submit(f"{base}/unschedule")).status_code == 404
    assert (await other_client.submit(f"{base}/delete")).status_code == 404

    post = await fresh(db, post_id)
    assert (post.title, post.content, post.status) == ("Post de teste", "Legenda de teste", "draft")
    assert media_files() == files_before


# ---------- legenda ----------


async def test_edit_caption_saves_and_shows_message(alice, db):
    client, post_id = alice
    resp = await client.submit(
        f"/dashboard/posts/{post_id}/edit", {"title": "  Novo título ", "content": "Nova legenda #promo"}
    )
    assert resp.status_code == 303 and resp.headers["location"].endswith("msg=saved")
    post = await fresh(db, post_id)
    assert (post.title, post.content) == ("Novo título", "Nova legenda #promo")
    assert "Legenda salva." in (await client.get(resp.headers["location"])).text


@pytest.mark.parametrize(
    ("title", "content", "expected"),
    [
        ("Título", "   ", "não pode ficar vazia"),
        ("  ", "texto", "Dê um título"),
        ("T" * 101, "texto", "no máximo 100"),
        ("Título", "a" * 2201, "2200"),
        ("Título", " ".join(f"#tag{i}" for i in range(31)), "31 hashtags"),
        ("Título", " ".join(f"#promoção{i}" for i in range(31)), "31 hashtags"),
    ],
    ids=["legenda-vazia", "titulo-vazio", "titulo-longo", "legenda-longa", "hashtags", "hashtags-acentuadas"],
)
async def test_invalid_captions_are_rejected_without_saving(alice, db, title, content, expected):
    client, post_id = alice
    resp = await client.submit(f"/dashboard/posts/{post_id}/edit", {"title": title, "content": content})
    assert resp.status_code == 400
    assert expected in resp.text
    post = await fresh(db, post_id)
    assert (post.title, post.content) == ("Post de teste", "Legenda de teste")


async def test_limits_are_inclusive(alice, db):
    client, post_id = alice
    content = "a" * (2200 - 31 * 5) + "".join(f" #t{i:03d}"[:5] for i in range(30)) + "x" * 0
    assert len(content) <= 2200
    resp = await client.submit(f"/dashboard/posts/{post_id}/edit", {"title": "T" * 100, "content": content})
    assert resp.status_code == 303


async def test_caption_html_is_escaped_in_editor_and_list(alice, db):
    client, post_id = alice
    evil = '</textarea><script>alert("xss")</script><img src=x onerror=alert(1)>'
    await client.submit(f"/dashboard/posts/{post_id}/edit", {"title": "<b>t</b>", "content": evil})
    for path in (f"/dashboard/posts/{post_id}/edit", "/dashboard/create"):
        page = await client.get(path)
        assert '<script>alert("xss")' not in page.text, path
        assert "<img src=x onerror" not in page.text, path


# ---------- agendamento ----------


async def test_schedule_requires_an_image(alice, db):
    client, post_id = alice
    resp = await client.submit(f"/dashboard/posts/{post_id}/schedule", {"scheduled_for": local_time_in(days=1)})
    assert resp.status_code == 400 and "Envie uma imagem" in resp.text
    assert (await fresh(db, post_id)).status == "draft"


@pytest.mark.parametrize(
    ("when", "expected"),
    [
        (lambda: local_time_in(days=-1), "pelo menos 5 minutos"),
        (lambda: local_time_in(minutes=1), "pelo menos 5 minutos"),
        (lambda: "amanhã de manhã", "inválidas"),
        (lambda: "2030-13-45T25:61", "inválidas"),
    ],
    ids=["passado", "daqui-a-1-minuto", "texto", "data-impossivel"],
)
async def test_schedule_rejects_bad_times(alice, db, when, expected):
    client, post_id = alice
    await client.upload(f"/dashboard/posts/{post_id}/image", make_image(800, 800))
    resp = await client.submit(f"/dashboard/posts/{post_id}/schedule", {"scheduled_for": when()})
    assert resp.status_code == 400 and expected in resp.text
    assert (await fresh(db, post_id)).status == "draft"


async def test_schedule_unschedule_and_reschedule_cycle(alice, db):
    client, post_id = alice
    await client.upload(f"/dashboard/posts/{post_id}/image", make_image(800, 800))

    ok = await client.submit(f"/dashboard/posts/{post_id}/schedule", {"scheduled_for": local_time_in(hours=2)})
    assert ok.status_code == 303 and ok.headers["location"] == "/dashboard/calendar"
    post = await fresh(db, post_id)
    assert post.status == "scheduled" and post.scheduled_for and post.scheduled_for > utcnow() + timedelta(hours=1)
    assert "Agendado para" in (await client.get(f"/dashboard/posts/{post_id}/edit")).text
    assert "Post de teste" in (await client.get("/dashboard/calendar")).text

    off = await client.submit(f"/dashboard/posts/{post_id}/unschedule")
    assert off.headers["location"].endswith("msg=unscheduled")
    post = await fresh(db, post_id)
    assert post.status == "draft" and post.scheduled_for is None
    assert "Post de teste" not in (await client.get("/dashboard/calendar")).text

    again = await client.submit(f"/dashboard/posts/{post_id}/schedule", {"scheduled_for": local_time_in(hours=3)})
    assert again.status_code == 303 and (await fresh(db, post_id)).status == "scheduled"


async def test_failed_post_can_be_scheduled_again(client: Client, db):
    await client.register("falha@exemplo.com")
    post_id = await make_post(
        db, "falha@exemplo.com", status="failed", image_key="posts/1/dddddddddddddddddddddddddddddddd.jpg"
    )
    resp = await client.submit(f"/dashboard/posts/{post_id}/schedule", {"scheduled_for": local_time_in(hours=1)})
    assert resp.status_code == 303 and (await fresh(db, post_id)).status == "scheduled"


async def test_removing_image_cancels_the_schedule_and_deletes_the_file(alice, db):
    client, post_id = alice
    await client.upload(f"/dashboard/posts/{post_id}/image", make_image(800, 800))
    await client.submit(f"/dashboard/posts/{post_id}/schedule", {"scheduled_for": local_time_in(hours=2)})
    assert len(media_files()) == 1

    resp = await client.submit(f"/dashboard/posts/{post_id}/image/remove")
    assert resp.headers["location"].endswith("msg=image_removed")
    post = await fresh(db, post_id)
    assert (post.image_key, post.status, post.scheduled_for) == (None, "draft", None)
    assert media_files() == []


async def test_deleting_a_post_deletes_its_image(alice, db):
    client, post_id = alice
    await client.upload(f"/dashboard/posts/{post_id}/image", make_image(800, 800))
    assert len(media_files()) == 1
    resp = await client.submit(f"/dashboard/posts/{post_id}/delete")
    assert resp.status_code == 303
    assert media_files() == []
    assert (await db.execute(select(Post).where(Post.id == post_id))).first() is None


@pytest.mark.parametrize("status", ["published", "publishing"])
async def test_published_posts_are_locked(client: Client, db, status):
    await client.register("trava@exemplo.com")
    key = "posts/1/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee.jpg"
    post_id = await make_post(db, "trava@exemplo.com", status=status, image_key=key)
    base = f"/dashboard/posts/{post_id}"

    for resp in (
        await client.submit(f"{base}/edit", {"title": "novo", "content": "novo"}),
        await client.upload(f"{base}/image", make_image(800, 800)),
        await client.submit(f"{base}/image/remove"),
        await client.submit(f"{base}/schedule", {"scheduled_for": local_time_in(days=1)}),
        await client.submit(f"{base}/unschedule"),
    ):
        assert resp.status_code == 409
    post = await fresh(db, post_id)
    assert (post.title, post.status, post.image_key) == ("Post de teste", status, key)
    assert media_files() == []


# ---------- listagem ----------


async def test_create_page_links_to_editor_and_shows_thumbnail(alice):
    client, post_id = alice
    await client.upload(f"/dashboard/posts/{post_id}/image", make_image(800, 800))
    page = await client.get("/dashboard/create")
    assert f'href="/dashboard/posts/{post_id}/edit"' in page.text
    assert "/media/posts/" in page.text
    assert "scheduleModal" not in page.text and "image_url" not in page.text


# ---------- do upload até a publicação ----------


async def test_uploaded_image_reaches_the_worker_as_a_public_url(alice, db, monkeypatch):
    client, post_id = alice
    await client.upload(f"/dashboard/posts/{post_id}/image", make_image(1000, 1000))
    user = (await db.execute(select(User).where(User.email == "alice@exemplo.com"))).scalar_one()
    db.add(BrandProfile(user_id=user.id, ig_access_token="EAAtoken", ig_account_id="1784"))
    post = await fresh(db, post_id)
    post.status, post.scheduled_for = "scheduled", utcnow() - timedelta(minutes=1)
    await db.commit()

    sent: list[dict] = []

    async def fake_publish(self, **kwargs):
        sent.append(kwargs)
        return "media_1"

    monkeypatch.setattr("app.instagram.service.InstagramService.publish_post", fake_publish)
    await worker.publish_scheduled_posts()

    assert len(sent) == 1
    url = sent[0]["image_url"]
    assert url.startswith("https://testserver/media/posts/") and url.endswith(".jpg")
    # É exatamente o que o Instagram vai baixar: precisa estar acessível e ser um JPEG
    fetched = await client.get(url.removeprefix("https://testserver"))
    assert fetched.status_code == 200 and open_image(fetched.content).format == "JPEG"
    assert (await fresh(db, post_id)).status == "published"


async def test_concurrent_uploads_do_not_mix_files(client: Client, other_client: Client, db):
    await client.register("a@exemplo.com")
    await other_client.register("b@exemplo.com")
    a = await make_post(db, "a@exemplo.com")
    b = await make_post(db, "b@exemplo.com")

    await asyncio.gather(
        client.upload(f"/dashboard/posts/{a}/image", make_image(800, 800, color=(255, 0, 0))),
        other_client.upload(f"/dashboard/posts/{b}/image", make_image(800, 800, color=(0, 0, 255))),
    )
    key_a = (await fresh(db, a)).image_key
    key_b = (await fresh(db, b)).image_key
    assert key_a and key_b and key_a != key_b
    assert len(media_files()) == 2
    red = open_image((MEDIA_ROOT / key_a).read_bytes()).getpixel((10, 10))
    blue = open_image((MEDIA_ROOT / key_b).read_bytes()).getpixel((10, 10))
    assert red[0] > 200 > red[2] and blue[2] > 200 > blue[0]
