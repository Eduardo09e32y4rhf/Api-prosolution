from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from payments.models import Payment

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    data = {"sub": "demo@prosolution", "plan": "free", "admin": False}
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": data})


@router.get("/dashboard/metrics")
async def dashboard_metrics(db: AsyncSession = Depends(get_db)):
    payments_total = (await db.execute(select(func.count(Payment.id)))).scalar() or 0
    revenue_total = (await db.execute(select(func.coalesce(func.sum(Payment.amount), 0)))).scalar() or 0

    return {
        "posts_total": 0,
        "payments_total": int(payments_total),
        "revenue_total": float(revenue_total),
        "last_post": None,
        "last_ai_action": None,
    }
