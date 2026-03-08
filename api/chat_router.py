from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db, save_message, load_history, get_all_sessions
from models.schemas import ChatRequest, ChatResponse, DesignRequest
from agents.orchestrator import run_orchestrator

router = APIRouter(prefix="/api/chat", tags=["chat"])


def build_prompt_from_form(req: DesignRequest) -> str:
    """
    Μετατρέπει τη δομημένη φόρμα σε structured prompt
    που καταλαβαίνει ο orchestrator.
    """
    prompt = f"""Design a complete system for the following project:

PROJECT DESCRIPTION:
{req.project_description}

TEAM SIZE:
{req.team_size}

SCALE:
{req.scale}

DEADLINE:
{req.deadline}

TECHNOLOGY CONSTRAINTS:
{req.tech_constraints}

CAPITAL CONSTRAINTS:
{req.capital_constraints}
"""
    if req.extra_details.strip():
        prompt += f"\nADDITIONAL DETAILS:\n{req.extra_details}"

    return prompt


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Ελεύθερο chat με τον assistant."""
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


@router.post("/design", response_model=ChatResponse)
async def design(request: DesignRequest, db: AsyncSession = Depends(get_db)):
    """
    Δέχεται δομημένη φόρμα, χτίζει prompt και τρέχει
    τον πλήρη pipeline των 4 agents.
    """
    prompt = build_prompt_from_form(request)

    history = await load_history(db, request.session_id)

    result = await run_orchestrator(
        user_message=prompt,
        history=history,
    )

    await save_message(db, request.session_id, "user", prompt)
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