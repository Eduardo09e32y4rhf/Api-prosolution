
from sqlalchemy import text
from app.database.session import AsyncSessionLocal

async def get_dashboard_metrics():
    async with AsyncSessionLocal() as session:
        total_posts = await session.execute(text("SELECT COUNT(*) FROM posts"))
        total_payments = await session.execute(text("SELECT COUNT(*) FROM payments"))
        revenue = await session.execute(text("SELECT COALESCE(SUM(amount),0) FROM payments"))
        last_post = await session.execute(text("SELECT created_at FROM posts ORDER BY created_at DESC LIMIT 1"))
        last_ai = await session.execute(text("SELECT created_at FROM ai_logs ORDER BY created_at DESC LIMIT 1"))

        return {
            "total_posts": total_posts.scalar() or 0,
            "total_payments": total_payments.scalar() or 0,
            "revenue": revenue.scalar() or 0,
            "last_post": str(last_post.scalar() or "—"),
            "last_ai_action": str(last_ai.scalar() or "—")
        }
