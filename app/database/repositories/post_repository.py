from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.post import InstagramPost

async def save_post(
    db: AsyncSession,
    instagram_id: str,
    image_url: str,
    caption: str
):
    post = InstagramPost(
        instagram_id=instagram_id,
        image_url=image_url,
        caption=caption
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post