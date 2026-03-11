from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import ConversationMessage


async def save_message(db: AsyncSession, session_id: str, role: str, content: str):
    msg = ConversationMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    await db.commit()


async def load_history(db: AsyncSession, session_id: str) -> list[dict]:
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.session_id == session_id)
        .order_by(ConversationMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in messages]


async def get_all_sessions(db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(ConversationMessage.session_id).distinct()
    )
    return [row[0] for row in result.fetchall()]