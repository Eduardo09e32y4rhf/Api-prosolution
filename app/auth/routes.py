from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.repositories.user_repo import UserRepository
from app.security import verify_password, create_token

router = APIRouter(tags=["Auth"])

@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    repo = UserRepository(db)
    user = await repo.get_by_email(email)

    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse("/?error=Credenciais+inválidas", status_code=302)

    token = create_token({"sub": user.email, "plan": getattr(user, "plan", "free")})
    resp = RedirectResponse("/dashboard", status_code=302)
    resp.set_cookie("token", token, httponly=True, secure=True, samesite="lax")
    return resp

@router.post("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("token")
    return resp

@router.post("/recover-password")
async def recover_password(
    email: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    repo = UserRepository(db)
    user = await repo.get_by_email(email)
    
    if not user:
        # Por segurança, retornamos a mesma mensagem para evitar enumeração
        return {"msg": "Se o email existir, um link de recuperação foi enviado."}
        
    # Gera um token com duração de 15 minutos (0.25 horas)
    token = create_token({"sub": user.email, "purpose": "password_reset"}, expires_delta_hours=0.25)
    
    link = f"http://localhost:8000/auth/reset-password?token={token}"
    print(f"==================================================")
    print(f"[SMTP SIMULADO] Email de recuperação para: {email}")
    print(f"[SMTP SIMULADO] Link: {link}")
    print(f"==================================================")
    
    return {"msg": "Se o email existir, um link de recuperação foi enviado.", "token_debug": token}

from pydantic import BaseModel
from app.security import hash_password
from fastapi import Body

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    import jwt
    from app.core.config import settings
    from app.security import ALGORITHM
    
    try:
        payload = jwt.decode(data.token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        purpose = payload.get("purpose")
        
        if email is None or purpose != "password_reset":
            raise HTTPException(status_code=401, detail="Token inválido")
            
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
        
    repo = UserRepository(db)
    user = await repo.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    user.password_hash = hash_password(data.new_password)
    await db.commit()
    
    return {"msg": "Senha redefinida com sucesso"}
