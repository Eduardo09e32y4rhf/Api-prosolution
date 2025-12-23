from fastapi import APIRouter, HTTPException
from app.instagram.service import publish_image
from app.instagram.schemas import InstagramPostRequest

router = APIRouter()

@router.post("/post")
def post_instagram(data: InstagramPostRequest):
    try:
        return publish_image(data.image_url, data.caption)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
