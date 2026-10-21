"""Processo separado que publica os posts agendados.

Execute com `python -m app.worker` (no docker-compose é o serviço `worker`).
Não rode dentro do processo web: com vários workers do Uvicorn o mesmo post sairia
mais de uma vez.
"""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.timeutils import utcnow
from app.database.models.brand_profile import BrandProfile
from app.database.models.post import Post
from app.database.session import AsyncSessionLocal
from app.instagram.service import InstagramService

logger = logging.getLogger(__name__)

BATCH_SIZE = 50


async def claim_due_posts() -> list[int]:
    """Marca os posts vencidos como 'publishing' e devolve seus IDs.

    No PostgreSQL o `FOR UPDATE SKIP LOCKED` garante que duas instâncias do worker
    nunca peguem o mesmo post.
    """
    async with AsyncSessionLocal() as db:
        posts = (
            (
                await db.execute(
                    select(Post)
                    .where(Post.status == "scheduled", Post.scheduled_for <= utcnow())
                    .order_by(Post.scheduled_for)
                    .limit(BATCH_SIZE)
                    .with_for_update(skip_locked=True)
                )
            )
            .scalars()
            .all()
        )
        for post in posts:
            post.status = "publishing"
        await db.commit()
        return [post.id for post in posts]


async def publish_post(post_id: int, ig_service: InstagramService) -> None:
    async with AsyncSessionLocal() as db:
        post = await db.get(Post, post_id)
        if post is None:
            return
        brand = (
            await db.execute(select(BrandProfile).where(BrandProfile.user_id == post.user_id))
        ).scalar_one_or_none()

        if not brand or not brand.ig_access_token or not brand.ig_account_id:
            logger.warning("Post %s falhou: conta do Instagram não vinculada.", post.id)
            post.status = "failed"
        elif not post.image_url:
            # A Graph API exige uma imagem pública para publicar no feed
            logger.warning("Post %s falhou: sem URL de imagem.", post.id)
            post.status = "failed"
        else:
            try:
                media_id = await ig_service.publish_post(
                    ig_account_id=brand.ig_account_id,
                    access_token=brand.ig_access_token,
                    image_url=post.image_url,
                    caption=post.content,
                )
                logger.info("Post %s publicado. IG Media ID: %s", post.id, media_id)
                post.status = "published"
            except Exception:
                logger.exception("Erro ao publicar post %s", post.id)
                post.status = "failed"
        await db.commit()


async def publish_scheduled_posts() -> None:
    post_ids = await claim_due_posts()
    if not post_ids:
        return
    ig_service = InstagramService()
    for post_id in post_ids:
        await publish_post(post_id, ig_service)


async def main() -> None:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(publish_scheduled_posts, "interval", minutes=1, max_instances=1, coalesce=True)
    scheduler.start()
    logger.info("Worker de publicação iniciado")
    await asyncio.Event().wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(main())
