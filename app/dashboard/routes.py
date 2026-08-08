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
async def dashboard(request: Request, user_token: dict = Depends(get_current_user_from_cookie), db: AsyncSession = Depends(get_db)):
    # 1. Buscar usuário real no banco para obter o ID
    from app.database.models.user import User
    from app.database.models.business import Business
    
    email = user_token.get("sub")
    user_db = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    
    if not user_db:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
    business = (await db.execute(select(Business).where(Business.user_id == user_db.id))).scalar_one_or_none()
    business_name = business.segment if business and business.segment else "Configurar Empresa"
    
    # 2. Buscar contagens filtrando por user_id
    posts_count = (await db.execute(select(func.count(Post.id)).where(Post.user_id == user_db.id))).scalar() or 0
    ai_logs_count = (await db.execute(select(func.count(AILog.id)).where(AILog.user_id == user_db.id))).scalar() or 0
    
    # Atividades recentes reais (posts gerados)
    recent_posts = (await db.execute(select(Post).where(Post.user_id == user_db.id).order_by(desc(Post.created_at)).limit(5))).scalars().all()
    
    activities = []
    for p in recent_posts:
        activities.append({
            "title": f"Post Gerado: {p.title}",
            "status": "Concluído",
            "status_color": "#10b981", 
            "date": p.created_at.strftime("%d/%m/%Y %H:%M")
        })
        
    metrics = {
        "instagram_status": "Não Conectado",
        "posts_this_month": posts_count,
        "ai_actions": ai_logs_count
    }
    
    user_data = {
        "email": user_db.email,
        "name": user_db.email.split("@")[0].capitalize(),
        "business_name": business_name,
        "plan": "Free" # Mudar para tabela de planos depois
    }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user_data,
        "metrics": metrics,
        "activities": activities,
        "active_menu": "home"
    })

# --- ROTAS PLACEHOLDER ---

@router.get("/create", response_class=HTMLResponse)
async def create_content(request: Request, user: dict = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("placeholder.html", {"request": request, "title": "Criar conteúdo", "active_menu": "create"})

@router.get("/calendar", response_class=HTMLResponse)
async def calendar(request: Request, user: dict = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("placeholder.html", {"request": request, "title": "Calendário", "active_menu": "calendar"})

@router.get("/instagram", response_class=HTMLResponse)
async def instagram(request: Request, user: dict = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("placeholder.html", {"request": request, "title": "Instagram", "active_menu": "instagram"})

@router.get("/subscription", response_class=HTMLResponse)
async def subscription(request: Request, user: dict = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("placeholder.html", {"request": request, "title": "Minha assinatura", "active_menu": "subscription"})

# --- CONFIGURAÇÕES ---

@router.get("/settings", response_class=HTMLResponse)
async def settings(request: Request, user_token: dict = Depends(get_current_user_from_cookie), db: AsyncSession = Depends(get_db)):
    from app.database.models.user import User
    from app.database.models.business import Business
    from app.database.models.brand_profile import BrandProfile
    
    email = user_token.get("sub")
    user_db = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    
    business = (await db.execute(select(Business).where(Business.user_id == user_db.id))).scalar_one_or_none()
    brand = (await db.execute(select(BrandProfile).where(BrandProfile.user_id == user_db.id))).scalar_one_or_none()
    
    user_data = {
        "email": user_db.email,
        "name": user_db.email.split("@")[0].capitalize(),
    }
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user_data,
        "business": business,
        "brand": brand,
        "active_menu": "settings"
    })

@router.post("/settings/business")
async def update_business(
    request: Request,
    user_token: dict = Depends(get_current_user_from_cookie),
    db: AsyncSession = Depends(get_db)
):
    from app.database.models.user import User
    from app.database.models.business import Business
    
    email = user_token.get("sub")
    user_db = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    
    form_data = await request.form()
    
    business = (await db.execute(select(Business).where(Business.user_id == user_db.id))).scalar_one_or_none()
    if not business:
        business = Business(user_id=user_db.id)
        db.add(business)
        
    business.segment = form_data.get("segment")
    business.products = form_data.get("products")
    business.services = form_data.get("services")
    business.audience = form_data.get("audience")
    business.city = form_data.get("city")
    business.whatsapp = form_data.get("whatsapp")
    business.objective = form_data.get("objective")
    
    await db.commit()
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/dashboard/settings?msg=empresa_salva", status_code=302)

@router.post("/settings/brand")
async def update_brand(
    request: Request,
    user_token: dict = Depends(get_current_user_from_cookie),
    db: AsyncSession = Depends(get_db)
):
    from app.database.models.user import User
    from app.database.models.brand_profile import BrandProfile
    
    email = user_token.get("sub")
    user_db = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    
    form_data = await request.form()
    
    brand = (await db.execute(select(BrandProfile).where(BrandProfile.user_id == user_db.id))).scalar_one_or_none()
    if not brand:
        brand = BrandProfile(user_id=user_db.id)
        db.add(brand)
        
    brand.tone = form_data.get("tone")
    brand.style = form_data.get("style")
    brand.emojis = True if form_data.get("emojis") == "on" else False
    brand.forbidden_words = form_data.get("forbidden_words")
    brand.cta = form_data.get("cta")
    
    await db.commit()
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/dashboard/settings?msg=marca_salva", status_code=302)
