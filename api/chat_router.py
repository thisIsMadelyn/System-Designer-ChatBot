from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from db.queries import save_message, load_history
from models.schemas import DesignRequest, MicroserviceOutput
from agents.orchestrator import run_orchestrator

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ── Request/Response models (local, no longer in schemas) ─────

class ChatRequest(BaseModel):
    message:    str
    session_id: str = "default"

class ChatResponse(BaseModel):
    session_id:       str
    answer:           str
    structured_output: Optional[MicroserviceOutput] = None


# ── Helpers ───────────────────────────────────────────────────

def build_prompt_from_form(req: DesignRequest) -> str:
    return req.build_prompt()


# ── Routes ────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Free-form chat with the assistant."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    history = await load_history(db, request.session_id)

    result = await run_orchestrator(
        user_message=request.message,
        history=history,
    )

    await save_message(db, request.session_id, "user",      request.message)
    await save_message(db, request.session_id, "assistant", result["response"])

    return ChatResponse(
        session_id=request.session_id,
        answer=result["response"],
        structured_output=result["structured_output"],
    )


@router.post("/design", response_model=ChatResponse)
async def design(request: DesignRequest, db: AsyncSession = Depends(get_db)):
    """Structured form → full 6-agent pipeline."""
    if not hasattr(request, "session_id"):
        session_id = "default"
    else:
        session_id = getattr(request, "session_id", "default")

    prompt  = build_prompt_from_form(request)
    history = await load_history(db, session_id)

    result = await run_orchestrator(
        user_message=prompt,
        history=history,
    )

    await save_message(db, session_id, "user",      prompt)
    await save_message(db, session_id, "assistant", result["response"])

    return ChatResponse(
        session_id=session_id,
        answer=result["response"],
        structured_output=result["structured_output"],
    )


@router.get("/history/{session_id}")
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    history = await load_history(db, session_id)
    return {"session_id": session_id, "messages": history}


@router.delete("/history/{session_id}")
async def clear_history(session_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete
    from db.models import ConversationMessage
    await db.execute(
        delete(ConversationMessage).where(
            ConversationMessage.session_id == session_id
        )
    )
    await db.commit()
    return {"message": f"History cleared for session {session_id}"}