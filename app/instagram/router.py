from fastapi import APIRouter
from app.instagram.post import router as post_router

router = APIRouter(prefix="/instagram", tags=["Instagram"])
router.include_router(post_router)
