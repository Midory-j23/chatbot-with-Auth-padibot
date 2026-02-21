from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from typing import AsyncGenerator

from database import get_db
from models.users_mdl import User
from models.chat_mdl import ChatSession, ChatMessage
from core.security import get_current_user
from schemas.chat_sch import SessionSummary, SessionDetail, SessionCreate, SessionUpdate, MessageOut, MessageCreate

router = APIRouter(tags=["chat"])

@router.get("/api/sessions", response_model=list[SessionSummary])
def list_user_sessions(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Optional: add last message preview
    for s in sessions:
        last_msg = (
            db.query(ChatMessage.message)
            .filter(ChatMessage.session_id == s.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
            .scalar()
        )
        s.last_message_preview = last_msg[:80] + "..." if last_msg and len(last_msg) > 80 else last_msg

    return sessions


@router.post("/api/sessions", response_model=SessionSummary, status_code=201)
def create_session(
    data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = ChatSession(
        user_id=current_user.id,
        title=data.title or "New Chat",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/api/sessions/{session_id}", response_model=SessionDetail)
def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "messages": messages,
    }


@router.post("/api/sessions/{session_id}/messages")
async def send_message_and_stream(
    session_id: int,
    msg: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    session_exists = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).scalar() is not None

    if not session_exists:
        raise HTTPException(404, "Conversation not found")

    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        sender="user",
        message=msg.message,
        # image=msg.image,   ← add column later if needed
    )
    db.add(user_msg)
    db.commit()

    # Update session timestamp
    db.execute(
        ChatSession.__table__.update()
        .where(ChatSession.id == session_id)
        .values(updated_at=func.now())
    )
    db.commit()

    async def generate() -> AsyncGenerator[str, None]:
        full_response = ""

        try:
            # -------------------------------
            # REPLACE THIS WITH YOUR REAL LLM CALL
            # Examples: Ollama, Groq, OpenAI, Anthropic, etc.
            # Must yield chunks as they arrive
            # -------------------------------
            # Placeholder example:
            fake_chunks = ["Hello", "! ", "This is ", "a ", "streaming ", "response ", "from ", "your ", "AI."]
            for chunk in fake_chunks:
                full_response += chunk
                yield f"data: {chunk}\n\n"

            # After streaming ends → save assistant message
            assistant_msg = ChatMessage(
                session_id=session_id,
                sender="assistant",
                message=full_response,
            )
            db.add(assistant_msg)
            db.commit()

            # Optional: auto-title after first real answer
            if db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count() <= 2:
                short_title = full_response.strip()[:60].rstrip(" .,!?") + "..."
                db.execute(
                    ChatSession.__table__.update()
                    .where(ChatSession.id == session_id)
                    .values(title=short_title)
                )
                db.commit()

        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"   # important for nginx proxy
        }
    )


@router.delete("/api/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(404, "Conversation not found")

    db.delete(session)  # cascade deletes messages
    db.flush()  # ensure DELETE is executed before commit
    db.commit()
    return None


@router.patch("/api/sessions/{session_id}", response_model=SessionSummary)
def update_session_title(
    session_id: int,
    data: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(404, "Conversation not found")

    session.title = data.title
    db.commit()
    db.refresh(session)
    return session