from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db, save_message, load_history, get_all_sessions
from models.schemas import ChatRequest, ChatResponse
from agents.orchestrator import run_orchestrator

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    history = await load_history(db, request.session_id)

    result = await run_orchestrator(
        user_message=request.message,
        history=history,
    )

    await save_message(db, request.session_id, "user", request.message)
    await save_message(db, request.session_id, "assistant", result["response"])

    return ChatResponse(
        session_id=request.session_id,
        answer=result["response"],
        structured_output=result["structured_output"],
    )


@router.get("/history/{session_id}")
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    history = await load_history(db, session_id)
    return {"session_id": session_id, "messages": history}


@router.get("/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    sessions = await get_all_sessions(db)
    return {"sessions": sessions}


@router.delete("/history/{session_id}")
async def clear_history(session_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete
    from db.database import ConversationMessage
    await db.execute(
        delete(ConversationMessage).where(
            ConversationMessage.session_id == session_id
        )
    )
    await db.commit()
    return {"message": f"History cleared for session {session_id}"}