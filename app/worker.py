import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database.session import AsyncSessionLocal
from app.database.models.post import Post
from app.database.models.brand_profile import BrandProfile
from app.instagram.service import InstagramService

logger = logging.getLogger(__name__)

async def publish_scheduled_posts():
    """Busca posts agendados que já passaram da hora e tenta publicar no Instagram."""
    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        # Busca todos os posts 'scheduled' onde a data de agendamento é <= agora
        posts = (await db.execute(
            select(Post).where(Post.status == "scheduled", Post.scheduled_for <= now)
        )).scalars().all()
        
        if not posts:
            return
            
        ig_service = InstagramService()
        
        for post in posts:
            try:
                # Pegar o BrandProfile do usuário para acessar o Token
                brand = (await db.execute(
                    select(BrandProfile).where(BrandProfile.user_id == post.user_id)
                )).scalar_one_or_none()
                
                if not brand or not brand.ig_access_token or not brand.ig_account_id:
                    logger.warning(f"Post {post.id} falhou: Conta do Instagram não vinculada.")
                    post.status = "failed"
                    await db.commit()
                    continue
                    
                # A API do Instagram exige uma URL de imagem válida.
                # Como a Prosolution pode gerar a imagem apenas na hora, ou já ter gerado:
                image_url = post.image_url
                if not image_url:
                    logger.warning(f"Post {post.id} falhou: Sem URL de imagem.")
                    post.status = "failed"
                    await db.commit()
                    continue
                    
                # Publicar!
                ig_media_id = await ig_service.publish_post(
                    ig_account_id=brand.ig_account_id,
                    access_token=brand.ig_access_token,
                    image_url=image_url,
                    caption=post.content
                )
                
                logger.info(f"Post {post.id} publicado com sucesso! IG Media ID: {ig_media_id}")
                post.status = "published"
                await db.commit()
                
            except Exception as e:
                logger.error(f"Erro ao publicar post {post.id}: {str(e)}")
                post.status = "failed"
                await db.commit()

# Inicializa o scheduler global
scheduler = AsyncIOScheduler()

def start_worker():
    """Inicia o cronjob."""
    # Roda a cada minuto
    scheduler.add_job(publish_scheduled_posts, 'interval', minutes=1)
    scheduler.start()
    logger.info("Worker de publicação iniciado!")
