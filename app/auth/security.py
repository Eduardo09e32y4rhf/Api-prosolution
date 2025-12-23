from fastapi import Depends, HTTPException, status

async def get_current_user():
    # 🔐 Placeholder simples (não quebra o sistema)
    return {"role": "admin"}
