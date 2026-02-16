from fastapi import APIRouter
from app.dashboard.repository import get_dashboard_metrics

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/metrics")
async def metrics():
    return await get_dashboard_metrics()
