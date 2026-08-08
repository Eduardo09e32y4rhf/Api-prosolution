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
async def create_content(request: Request, user_token: dict = Depends(get_current_user_from_cookie), db: AsyncSession = Depends(get_db)):
    from app.database.models.user import User
    from app.database.models.business import Business
    
    email = user_token.get("sub")
    user_db = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    
    if not user_db:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
    business = (await db.execute(select(Business).where(Business.user_id == user_db.id))).scalar_one_or_none()
    has_setup = True if business and business.segment else False
    
    posts = (await db.execute(select(Post).where(Post.user_id == user_db.id).order_by(desc(Post.created_at)))).scalars().all()
    
    user_data = {
        "email": user_db.email,
        "name": user_db.email.split("@")[0].capitalize(),
    }
    
    return templates.TemplateResponse("create.html", {
        "request": request, 
        "user": user_data,
        "has_setup": has_setup,
        "posts": posts,
        "active_menu": "create"
    })

@router.post("/create/generate")
async def generate_content(
    request: Request,
    user_token: dict = Depends(get_current_user_from_cookie),
    db: AsyncSession = Depends(get_db)
):
    from app.database.models.user import User
    from app.database.models.business import Business
    from app.database.models.brand_profile import BrandProfile
    from app.ai.engine import AIEngine
    
    email = user_token.get("sub")
    user_db = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    
    business = (await db.execute(select(Business).where(Business.user_id == user_db.id))).scalar_one_or_none()
    brand = (await db.execute(select(BrandProfile).where(BrandProfile.user_id == user_db.id))).scalar_one_or_none()
    
    form_data = await request.form()
    topic = form_data.get("topic")
    details = form_data.get("details", "")
    
    full_topic = f"{topic}. Detalhes adicionais: {details}" if details else topic
    
    # Executa a IA
    ai = AIEngine()
    generated_content = await ai.generate_post(business, brand, full_topic)
    
    # Salva o Log da IA
    ai_log = AILog(
        user_id=user_db.id,
        provider="openai",
        prompt=full_topic,
        response=generated_content
    )
    db.add(ai_log)
    
    # Salva o Post como Rascunho
    new_post = Post(
        user_id=user_db.id,
        title=topic[:50] + "..." if len(topic) > 50 else topic,
        content=generated_content,
        platform="instagram"
    )
    db.add(new_post)
    
    await db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/dashboard/create", status_code=302)

@router.get("/calendar", response_class=HTMLResponse)
async def calendar(request: Request, user_token: dict = Depends(get_current_user_from_cookie), db: AsyncSession = Depends(get_db)):
    from app.database.models.user import User
    
    email = user_token.get("sub")
    user_db = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    
    posts = (await db.execute(select(Post).where(Post.user_id == user_db.id, Post.status == "scheduled"))).scalars().all()
    
    user_data = {
        "email": user_db.email,
        "name": user_db.email.split("@")[0].capitalize(),
    }
    
    return templates.TemplateResponse("calendar.html", {
        "request": request,
        "user": user_data,
        "posts": posts,
        "active_menu": "calendar"
    })

@router.post("/posts/{post_id}/schedule")
async def schedule_post(
    post_id: int,
    request: Request,
    user_token: dict = Depends(get_current_user_from_cookie),
    db: AsyncSession = Depends(get_db)
):
    from app.database.models.user import User
    email = user_token.get("sub")
    user_db = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    
    post = (await db.execute(select(Post).where(Post.id == post_id, Post.user_id == user_db.id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
        
    form_data = await request.form()
    scheduled_for_str = form_data.get("scheduled_for")
    
    try:
        # Formato esperado: YYYY-MM-DDTHH:MM
        dt = datetime.strptime(scheduled_for_str, "%Y-%m-%dT%H:%M")
        post.scheduled_for = dt
        post.status = "scheduled"
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Data inválida")
        
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/dashboard/calendar", status_code=302)

@router.post("/posts/{post_id}/delete")
async def delete_post(
    post_id: int,
    user_token: dict = Depends(get_current_user_from_cookie),
    db: AsyncSession = Depends(get_db)
):
    from app.database.models.user import User
    email = user_token.get("sub")
    user_db = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    
    post = (await db.execute(select(Post).where(Post.id == post_id, Post.user_id == user_db.id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
        
    await db.delete(post)
    await db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/dashboard/create", status_code=302)

@router.get("/instagram", response_class=HTMLResponse)
async def instagram_view(request: Request, user_token: dict = Depends(get_current_user_from_cookie), db: AsyncSession = Depends(get_db)):
    from app.database.models.user import User
    from app.database.models.brand_profile import BrandProfile
    
    email = user_token.get("sub")
    user_db = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    brand = (await db.execute(select(BrandProfile).where(BrandProfile.user_id == user_db.id))).scalar_one_or_none()
    
    is_connected = False
    if brand and brand.ig_access_token and brand.ig_account_id:
        is_connected = True
        
    user_data = {
        "email": user_db.email,
        "name": user_db.email.split("@")[0].capitalize(),
    }
    
    return templates.TemplateResponse("instagram.html", {
        "request": request, 
        "user": user_data,
        "is_connected": is_connected,
        "active_menu": "instagram"
    })

@router.get("/instagram/connect")
async def instagram_connect():
    from app.instagram.service import InstagramService
    ig_service = InstagramService()
    url = ig_service.get_authorization_url()
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url)

@router.get("/instagram/callback")
async def instagram_callback(
    code: str,
    request: Request,
    user_token: dict = Depends(get_current_user_from_cookie),
    db: AsyncSession = Depends(get_db)
):
    from app.instagram.service import InstagramService
    from app.database.models.user import User
    from app.database.models.brand_profile import BrandProfile
    from fastapi.responses import RedirectResponse
    
    try:
        ig_service = InstagramService()
        access_token = await ig_service.exchange_code_for_token(code)
        account_id = await ig_service.get_instagram_business_account_id(access_token)
        
        email = user_token.get("sub")
        user_db = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        brand = (await db.execute(select(BrandProfile).where(BrandProfile.user_id == user_db.id))).scalar_one_or_none()
        
        if not brand:
            brand = BrandProfile(user_id=user_db.id)
            db.add(brand)
            
        brand.ig_access_token = access_token
        brand.ig_account_id = account_id
        await db.commit()
        
        return RedirectResponse("/dashboard/instagram")
        
    except Exception as e:
        return RedirectResponse(f"/dashboard/instagram?error={str(e)}")

@router.post("/instagram/disconnect")
async def instagram_disconnect(
    user_token: dict = Depends(get_current_user_from_cookie),
    db: AsyncSession = Depends(get_db)
):
    from app.database.models.user import User
    from app.database.models.brand_profile import BrandProfile
    from fastapi.responses import RedirectResponse
    
    email = user_token.get("sub")
    user_db = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    brand = (await db.execute(select(BrandProfile).where(BrandProfile.user_id == user_db.id))).scalar_one_or_none()
    
    if brand:
        brand.ig_access_token = None
        brand.ig_account_id = None
        await db.commit()
        
    return RedirectResponse("/dashboard/instagram")

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
