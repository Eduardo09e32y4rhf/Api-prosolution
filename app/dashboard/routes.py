from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database.session import get_db
from app.database.models.post import Post
from app.database.models.payment import Payment
from app.database.models.ai_log import AILog
from app.security import get_current_user_from_cookie

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(get_current_user_from_cookie), db: AsyncSession = Depends(get_db)):
    # Buscar contagens e métricas reais do banco
    posts_count = (await db.execute(select(func.count(Post.id)))).scalar() or 0
    payments_total = (await db.execute(select(func.coalesce(func.sum(Payment.amount), 0.0)))).scalar() or 0.0
    ai_logs_count = (await db.execute(select(func.count(AILog.id)))).scalar() or 0
    
    # Atividades recentes reais
    recent_posts = (await db.execute(select(Post).order_by(desc(Post.created_at)).limit(3))).scalars().all()
    recent_payments = (await db.execute(select(Payment).order_by(desc(Payment.created_at)).limit(3))).scalars().all()
    
    activities = []
    for p in recent_posts:
        activities.append({
            "title": f"Post Gerado: {p.title}",
            "status": "Concluído",
            "status_color": "#10b981", # Verde vibrante
            "date": p.created_at.strftime("%d/%m/%Y %H:%M")
        })
        
    for pay in recent_payments:
        activities.append({
            "title": f"Pagamento Pix: R$ {pay.amount:.2f}",
            "status": pay.status.capitalize(),
            "status_color": "#3b82f6" if pay.status == "approved" else "#f59e0b",
            "date": pay.created_at.strftime("%d/%m/%Y %H:%M")
        })
        
    metrics = {
        "followers": "0",
        "posts": posts_count,
        "revenue": f"R$ {payments_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "ai_actions": ai_logs_count
    }
    
    user_data = {
        "email": user.get("sub", "Usuário"),
        "name": user.get("sub", "Usuário").split("@")[0].capitalize(),
        "plan": user.get("plan", "Free").capitalize()
    }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user_data,
        "metrics": metrics,
        "activities": activities
    })
