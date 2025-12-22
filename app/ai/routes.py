from fastapi import APIRouter
from app.ai.orchestrator import generate_instagram_content
from app.ai.admin.system_admin import evaluate_system

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/instagram-content")
def instagram_content(topic: str):
    return generate_instagram_content(topic)

@router.post("/admin-review")
def admin_review(system_snapshot: dict):
    return {"admin_prompt": evaluate_system(system_snapshot)}
