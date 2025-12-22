from fastapi import APIRouter, HTTPException
from app.instagram.schemas import InstagramPostRequest
from app.instagram.service import publish_image

router = APIRouter()


@router.post("/post")
def instagram_post(data: InstagramPostRequest):
    try:
        return publish_image(
            image_url=str(data.image_url),  # 👈 conversão correta
            caption=data.caption,
        )
    except Exception as e:
        # Retorna o erro real (sem mascarar)
        raise HTTPException(status_code=500, detail=str(e))