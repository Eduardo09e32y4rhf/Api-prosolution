
from datetime import datetime
from app.database.session import AsyncSessionLocal
from app.database.models.ai_log import AILog

async def evaluate_system():
    return {
        "status": "ok",
        "checked_at": datetime.utcnow().isoformat()
    }

async def log_ai_action(action: str):
    async with AsyncSessionLocal() as session:
        log = AILog(action=action)
        session.add(log)
        await session.commit()
