# from fastapi import APIRouter, Depends, HTTPException, status, Request
# from fastapi.responses import StreamingResponse
# from sqlalchemy.orm import Session
# from sqlalchemy import func, select
# from typing import AsyncGenerator

# from database import get_db
# from models.users_mdl import User
# from models.chat_mdl import ChatSession, ChatMessage
# from core.security import get_current_user
# from schemas.chat_sch import SessionSummary, SessionDetail, SessionCreate, SessionUpdate, MessageOut, MessageCreate

# router = APIRouter(tags=["chat"])

# @router.get("/api/sessions", response_model=list[SessionSummary])
# def list_user_sessions(
#     limit: int = 50,
#     offset: int = 0,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     sessions = (
#         db.query(ChatSession)
#         .filter(ChatSession.user_id == current_user.id)
#         .order_by(ChatSession.updated_at.desc())
#         .offset(offset)
#         .limit(limit)
#         .all()
#     )

#     # Optional: add last message preview
#     for s in sessions:
#         last_msg = (
#             db.query(ChatMessage.message)
#             .filter(ChatMessage.session_id == s.id)
#             .order_by(ChatMessage.created_at.desc())
#             .limit(1)
#             .scalar()
#         )
#         s.last_message_preview = last_msg[:80] + "..." if last_msg and len(last_msg) > 80 else last_msg

#     return sessions


# @router.post("/api/sessions", response_model=SessionSummary, status_code=201)
# def create_session(
#     data: SessionCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     session = ChatSession(
#         user_id=current_user.id,
#         title=data.title or "New Chat",
#     )
#     db.add(session)
#     db.commit()
#     db.refresh(session)
#     return session


# @router.get("/api/sessions/{session_id}", response_model=SessionDetail)
# def get_session_detail(
#     session_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     session = db.query(ChatSession).filter(
#         ChatSession.id == session_id,
#         ChatSession.user_id == current_user.id
#     ).first()

#     if not session:
#         raise HTTPException(status_code=404, detail="Conversation not found")

#     messages = (
#         db.query(ChatMessage)
#         .filter(ChatMessage.session_id == session_id)
#         .order_by(ChatMessage.created_at.asc())
#         .all()
#     )

#     return {
#         "id": session.id,
#         "title": session.title,
#         "created_at": session.created_at,
#         "updated_at": session.updated_at,
#         "messages": messages,
#     }


# @router.post("/api/sessions/{session_id}/messages")
# async def send_message_and_stream(
#     session_id: int,
#     msg: MessageCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     # Verify ownership
#     session_exists = db.query(ChatSession).filter(
#         ChatSession.id == session_id,
#         ChatSession.user_id == current_user.id
#     ).scalar() is not None

#     if not session_exists:
#         raise HTTPException(404, "Conversation not found")

#     # Save user message
#     user_msg = ChatMessage(
#         session_id=session_id,
#         sender="user",
#         message=msg.message,
#         # image=msg.image,   ← add column later if needed
#     )
#     db.add(user_msg)
#     db.commit()

#     # Update session timestamp
#     db.execute(
#         ChatSession.__table__.update()
#         .where(ChatSession.id == session_id)
#         .values(updated_at=func.now())
#     )
#     db.commit()

#     async def generate() -> AsyncGenerator[str, None]:
#         full_response = ""

#         try:
#             # -------------------------------
#             # REPLACE THIS WITH YOUR REAL LLM CALL
#             # Examples: Ollama, Groq, OpenAI, Anthropic, etc.
#             # Must yield chunks as they arrive
#             # -------------------------------
#             # Placeholder example:
#             fake_chunks = ["Hello", "! ", "This is ", "a ", "streaming ", "response ", "from ", "your ", "AI."]
#             for chunk in fake_chunks:
#                 full_response += chunk
#                 yield f"data: {chunk}\n\n"

#             # After streaming ends → save assistant message
#             assistant_msg = ChatMessage(
#                 session_id=session_id,
#                 sender="assistant",
#                 message=full_response,
#             )
#             db.add(assistant_msg)
#             db.commit()

#             # Optional: auto-title after first real answer
#             if db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count() <= 2:
#                 short_title = full_response.strip()[:60].rstrip(" .,!?") + "..."
#                 db.execute(
#                     ChatSession.__table__.update()
#                     .where(ChatSession.id == session_id)
#                     .values(title=short_title)
#                 )
#                 db.commit()

#         except Exception as e:
#             yield f"data: [ERROR] {str(e)}\n\n"

#     return StreamingResponse(
#         generate(),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "Connection": "keep-alive",
#             "X-Accel-Buffering": "no"   # important for nginx proxy
#         }
#     )


# @router.delete("/api/sessions/{session_id}", status_code=204)
# def delete_session(
#     session_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     session = db.query(ChatSession).filter(
#         ChatSession.id == session_id,
#         ChatSession.user_id == current_user.id
#     ).first()

#     if not session:
#         raise HTTPException(404, "Conversation not found")

#     db.delete(session)  # cascade deletes messages
#     db.flush()  # ensure DELETE is executed before commit
#     db.commit()
#     return None


# @router.patch("/api/sessions/{session_id}", response_model=SessionSummary)
# def update_session_title(
#     session_id: int,
#     data: SessionUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     session = db.query(ChatSession).filter(
#         ChatSession.id == session_id,
#         ChatSession.user_id == current_user.id
#     ).first()

#     if not session:
#         raise HTTPException(404, "Conversation not found")

#     session.title = data.title
#     db.commit()
#     db.refresh(session)
#     return session



# from fastapi import APIRouter, Depends, HTTPException, status, Request
# from fastapi.responses import StreamingResponse
# from sqlalchemy.orm import Session
# from sqlalchemy import func, select
# from typing import AsyncGenerator
# import httpx
# import json

# from database import get_db
# from models.users_mdl import User
# from models.chat_mdl import ChatSession, ChatMessage
# from core.security import get_current_user
# from schemas.chat_sch import SessionSummary, SessionDetail, SessionCreate, SessionUpdate, MessageOut, MessageCreate
# from pydantic import BaseModel

# router = APIRouter(tags=["chat"])

# # Ollama configuration
# OLLAMA_URL = "http://localhost:11434"  # Default Ollama URL
# OLLAMA_MODEL = "gemma3"
# AVAILABLE_MODELS = ["gemma3", "llama2", "mistral", "codellama", "phi"]

# # Change to your downloaded model (e.g., "mistral", "llama2", "codellama")

# @router.get("/api/sessions", response_model=list[SessionSummary])
# def list_user_sessions(
#     limit: int = 50,
#     offset: int = 0,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
    
# ):
#     sessions = (
#         db.query(ChatSession)
#         .filter(ChatSession.user_id == current_user.id)
#         .order_by(ChatSession.updated_at.desc())
#         .offset(offset)
#         .limit(limit)
#         .all()
#     )

#     # Optional: add last message preview
#     for s in sessions:
#         last_msg = (
#             db.query(ChatMessage.message)
#             .filter(ChatMessage.session_id == s.id)
#             .order_by(ChatMessage.created_at.desc())
#             .limit(1)
#             .scalar()
#         )
#         s.last_message_preview = last_msg[:80] + "..." if last_msg and len(last_msg) > 80 else last_msg

#     return sessions


# @router.post("/api/sessions", response_model=SessionSummary, status_code=201)
# def create_session(
#     data: SessionCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     session = ChatSession(
#         user_id=current_user.id,
#         title=data.title or "New Chat",
#     )
#     db.add(session)
#     db.commit()
#     db.refresh(session)
#     return session


# @router.get("/api/sessions/{session_id}", response_model=SessionDetail)
# def get_session_detail(
#     session_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     session = db.query(ChatSession).filter(
#         ChatSession.id == session_id,
#         ChatSession.user_id == current_user.id
#     ).first()

#     if not session:
#         raise HTTPException(status_code=404, detail="Conversation not found")

#     messages = (
#         db.query(ChatMessage)
#         .filter(ChatMessage.session_id == session_id)
#         .order_by(ChatMessage.created_at.asc())
#         .all()
#     )

#     return {
#         "id": session.id,
#         "title": session.title,
#         "created_at": session.created_at,
#         "updated_at": session.updated_at,
#         "messages": messages,
#     }


# async def get_conversation_history(session_id: int, db: Session, max_messages: int = 10):
#     """Get previous messages to provide context to Ollama"""
#     messages = (
#         db.query(ChatMessage)
#         .filter(ChatMessage.session_id == session_id)
#         .order_by(ChatMessage.created_at.desc())
#         .limit(max_messages)
#         .all()
#     )
    
#     # Reverse to get chronological order
#     messages.reverse()
    
#     # Format for Ollama
#     history = []
#     for msg in messages:
#         role = "user" if msg.sender == "user" else "assistant"
#         history.append({
#             "role": role,
#             "content": msg.message
#         })
    
#     return history


# @router.post("/api/sessions/{session_id}/messages")
# async def send_message_and_stream(
#     session_id: int,
#     msg: MessageCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     # Verify ownership
#     session = db.query(ChatSession).filter(
#         ChatSession.id == session_id,
#         ChatSession.user_id == current_user.id
#     ).first()

#     if not session:
#         raise HTTPException(404, "Conversation not found")

#     # Save user message
#     user_msg = ChatMessage(
#         session_id=session_id,
#         sender="user",
#         message=msg.message,
#     )
#     db.add(user_msg)
#     db.commit()

#     # Update session timestamp
#     db.execute(
#         ChatSession.__table__.update()
#         .where(ChatSession.id == session_id)
#         .values(updated_at=func.now())
#     )
#     db.commit()

#     # Get conversation history
#     conversation_history = await get_conversation_history(session_id, db)

#     async def generate() -> AsyncGenerator[str, None]:
#         full_response = ""
        
#         try:
#             # Prepare the request for Ollama
#             ollama_request = {
#                 "model": OLLAMA_MODEL,
#                 "messages": conversation_history,
#                 "stream": True,
#                 "options": {
#                     "temperature": 0.7,
#                     "top_p": 0.9,
#                 }
#             }
            
#             # Make streaming request to Ollama
#             async with httpx.AsyncClient(timeout=60.0) as client:
#                 async with client.stream(
#                     "POST",
#                     f"{OLLAMA_URL}/api/chat",
#                     json=ollama_request
#                 ) as response:
#                     response.raise_for_status()
                    
#                     async for line in response.aiter_lines():
#                         if line.strip():
#                             try:
#                                 chunk_data = json.loads(line)
#                                 if "message" in chunk_data and "content" in chunk_data["message"]:
#                                     content_chunk = chunk_data["message"]["content"]
#                                     full_response += content_chunk
#                                     yield f"data: {content_chunk}\n\n"
                                
#                                 if chunk_data.get("done", False):
#                                     break
                                    
#                             except json.JSONDecodeError:
#                                 continue
            
#             # After streaming ends → save assistant message
#             if full_response.strip():
#                 assistant_msg = ChatMessage(
#                     session_id=session_id,
#                     sender="assistant",
#                     message=full_response,
#                 )
#                 db.add(assistant_msg)
#                 db.commit()

#                 # Generate title ONLY for new conversations (first exchange)
#                 message_count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
                
#                 # If this is the first assistant response (message_count should be 2: user + assistant)
#                 if message_count == 2 and (not session.title or session.title == "New Chat"):
#                     # Generate a title based on the user's first message
#                     user_first_message = msg.message
                    
#                     # Method 1: Simple truncation (fastest)
#                     short_title = user_first_message.strip()[:40].strip()
#                     if len(user_first_message) > 40:
#                         short_title += "..."
                    
#                     # Method 2: Use Ollama to generate a better title (uncomment if you want AI-generated titles)
#                     # try:
#                     #     title_prompt = f"Generate a very short title (max 6 words) for a conversation that starts with: '{user_first_message[:100]}'. Return ONLY the title, no quotes, no extra text."
#                     #     
#                     #     title_request = {
#                     #         "model": OLLAMA_MODEL,
#                     #         "messages": [{"role": "user", "content": title_prompt}],
#                     #         "stream": False,
#                     #         "options": {
#                     #             "temperature": 0.3,
#                     #             "num_predict": 20
#                     #         }
#                     #     }
#                     #     
#                     #     async with httpx.AsyncClient(timeout=10.0) as title_client:
#                     #         title_response = await title_client.post(
#                     #             f"{OLLAMA_URL}/api/chat",
#                     #             json=title_request
#                     #         )
#                     #         if title_response.status_code == 200:
#                     #             title_data = title_response.json()
#                     #             ai_title = title_data.get("message", {}).get("content", "").strip()
#                     #             if ai_title and len(ai_title) < 60:
#                     #                 short_title = ai_title
#                     # except Exception as e:
#                     #     print(f"Title generation failed: {e}")
#                     #     # Fall back to truncated message
                    
#                     # Update the session title
#                     db.execute(
#                         ChatSession.__table__.update()
#                         .where(ChatSession.id == session_id)
#                         .values(title=short_title)
#                     )
#                     db.commit()
            
#             yield f"data: [DONE]\n\n"
            
#         except Exception as e:
#             yield f"data: [ERROR] {str(e)}\n\n"

#     return StreamingResponse(
#         generate(),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "Connection": "keep-alive",
#             "X-Accel-Buffering": "no"
#         }
#     )
    
# @router.delete("/api/sessions/{session_id}", status_code=204)
# def delete_session(
#     session_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     session = db.query(ChatSession).filter(
#         ChatSession.id == session_id,
#         ChatSession.user_id == current_user.id
#     ).first()

#     if not session:
#         raise HTTPException(404, "Conversation not found")

#     db.delete(session)
#     db.flush()
#     db.commit()
#     return None


# @router.patch("/api/sessions/{session_id}", response_model=SessionSummary)
# def update_session_title(
#     session_id: int,
#     data: SessionUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     session = db.query(ChatSession).filter(
#         ChatSession.id == session_id,
#         ChatSession.user_id == current_user.id
#     ).first()

#     if not session:
#         raise HTTPException(404, "Conversation not found")

#     session.title = data.title
#     db.commit()
#     db.refresh(session)
#     return session


# # Optional: Add an endpoint to list available Ollama models
# @router.get("/api/ollama/models")
# async def list_ollama_models():
#     """Get list of available models from Ollama"""
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(f"{OLLAMA_URL}/api/tags")
#             if response.status_code == 200:
#                 return response.json()
#             else:
#                 return {"error": "Could not fetch models"}
#     except Exception as e:
#         return {"error": str(e)}
    
    
    
    
# edited---------------------------

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from typing import AsyncGenerator, Optional
import asyncio
import httpx
import json
import uuid
import os

from database import get_db
from models.users_mdl import User
from models.chat_mdl import ChatSession, ChatMessage
from core.security import get_current_user
from schemas.chat_sch import SessionSummary, SessionDetail, SessionCreate, SessionUpdate, MessageOut, MessageCreate
from pydantic import BaseModel

router = APIRouter(tags=["chat"])

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"  # Default Ollama URL
OLLAMA_MODEL = "gemma3:latest"
AVAILABLE_MODELS = ["gemma3:latest", "qwen3:4b"]
# Use 0 to avoid CUDA crashes on systems with broken GPU drivers (Windows)
OLLAMA_NUM_GPU = int(os.getenv("OLLAMA_NUM_GPU", "0"))

_stream_cancel_events: dict[int, asyncio.Event] = {}
_stream_generation_ids: dict[int, str] = {}


def _get_last_message(session_id: int, db: Session) -> Optional[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .first()
    )


def _remove_trailing_assistant_message(session_id: int, db: Session) -> None:
    """Remove only an incomplete assistant reply — never the user's message."""
    last = _get_last_message(session_id, db)
    if last and last.sender == "assistant":
        db.delete(last)
        db.commit()


# ChatRequest model for handling model selection
class ReplyToPayload(BaseModel):
    content: str
    role: str = "assistant"  # "user" | "assistant"


class ChatRequest(BaseModel):
    message: str
    image: Optional[str] = None
    model: Optional[str] = None
    reply_to: Optional[ReplyToPayload] = None


REPLY_START = "<<<REPLY>>>"
REPLY_END = "<<<END_REPLY>>>"


def _strip_reply_markers(raw: str) -> tuple[str, Optional[dict]]:
    """Return (plain_message, reply_meta) from a stored message string."""
    if not raw.startswith(REPLY_START):
        return raw, None

    end_marker = f"\n{REPLY_END}\n"
    end_idx = raw.find(end_marker)
    if end_idx == -1:
        return raw, None

    header_and_quote = raw[len(REPLY_START):end_idx]
    body = raw[end_idx + len(end_marker):]
    nl = header_and_quote.find("\n")
    if nl == -1:
        return raw, None

    role = header_and_quote[:nl].strip()
    quote = header_and_quote[nl + 1:].strip()
    return body, {"role": role, "content": quote}


def _format_user_message_for_model(raw_message: str, reply_to: Optional[ReplyToPayload] = None) -> str:
    """Build the user turn sent to Ollama, highlighting an explicit reply target."""
    body, embedded = _strip_reply_markers(raw_message)
    reply_meta = None
    if reply_to and reply_to.content.strip():
        reply_meta = {"role": reply_to.role, "content": reply_to.content.strip()}
    elif embedded:
        reply_meta = embedded

    if not reply_meta:
        return body

    who = "the user" if reply_meta["role"] == "user" else "the assistant"
    return (
        f'The user is specifically replying to this earlier message from {who}:\n'
        f'"""\n{reply_meta["content"]}\n"""\n\n'
        f"User's reply:\n{body}"
    )

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


async def get_conversation_history(
    session_id: int,
    db: Session,
    max_messages: int = 40,
    model_name: Optional[str] = None,
):
    """
    Build chat history for Ollama so follow-up messages use prior context.
    Uses message id for stable order and keeps a clean user/assistant sequence.
    """
    db.expire_all()

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )

    # Keep only the most recent N messages for the model context window
    if len(messages) > max_messages:
        messages = messages[-max_messages:]

    active_model = (model_name or OLLAMA_MODEL).strip() or OLLAMA_MODEL
    base = active_model.split(":")[0].lower()

    if base.startswith("qwen3"):
        identity = "Qwen 3"
    elif base.startswith("qwen"):
        identity = "Qwen"
    elif base.startswith("gemma3"):
        identity = "Gemma 3"
    elif base.startswith("gemma2"):
        identity = "Gemma 2"
    elif base.startswith("gemma"):
        identity = "Gemma"
    else:
        identity = base

    history = [
        {
            "role": "system",
            "content": (
                f"You are {identity}, a helpful AI assistant. "
                "Answer the user's latest message directly and helpfully. "
                "If older user messages were never answered (for example the user pressed Stop), "
                "ignore those unfinished requests unless the user asks about them again. "
                "Do NOT introduce yourself or mention your model name in every reply. "
                "Only say who you are if the user explicitly asks (e.g. who are you / تو کی هستی). "
                "Never write raw model tags like gemma3:latest in your answers. "
                "Reply in the same language the user writes in."
            ),
        }
    ]

    last_role = None
    for msg in messages:
        content = (msg.message or "").strip()
        if not content:
            continue

        role = "user" if msg.sender == "user" else "assistant"
        if role == "user":
            content = _format_user_message_for_model(content)

        # Merge consecutive same-role messages so Ollama gets a clean turn sequence
        if last_role == role and history and history[-1]["role"] == role:
            if role == "user":
                # After Stop, several user lines can stack — mark older ones as interrupted
                history[-1]["content"] += (
                    "\n\n(earlier message, may have been interrupted — do not answer unless relevant)\n"
                    + content
                )
            else:
                history[-1]["content"] += "\n\n" + content
            continue

        history.append({"role": role, "content": content})
        last_role = role

    if history and history[-1]["role"] == "user":
        history[-1]["content"] += (
            "\n\n(Respond only to the latest user message above. "
            "Do not restart older interrupted requests.)"
        )

    return history


@router.post("/api/sessions/{session_id}/messages")
async def send_message_and_stream(
    session_id: int,
    msg: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(404, "Conversation not found")

    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        sender="user",
        message=msg.message,
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

    # Get selected model or use default
    selected_model = (msg.model or "").strip() or OLLAMA_MODEL
    print(f"[chat] session={session_id} using model={selected_model!r} (requested={msg.model!r})")

    # Get conversation history (system prompt includes current model identity)
    conversation_history = await get_conversation_history(
        session_id,
        db,
        model_name=selected_model,
    )

    # Make sure the latest user turn highlights the replied-to message for the model
    if msg.reply_to and conversation_history:
        for i in range(len(conversation_history) - 1, -1, -1):
            if conversation_history[i]["role"] == "user":
                conversation_history[i]["content"] = _format_user_message_for_model(
                    msg.message,
                    msg.reply_to,
                )
                break

    if session_id in _stream_cancel_events:
        _stream_cancel_events[session_id].set()

    cancel_event = asyncio.Event()
    _stream_cancel_events[session_id] = cancel_event
    generation_id = str(uuid.uuid4())
    _stream_generation_ids[session_id] = generation_id

    async def generate() -> AsyncGenerator[str, None]:
        full_response = ""
        full_thinking = ""
        cancelled = False
        thinking_phase = True

        def is_stale_or_cancelled() -> bool:
            return (
                cancelled
                or cancel_event.is_set()
                or _stream_generation_ids.get(session_id) != generation_id
            )

        try:
            # Tell the client which model is actually answering
            yield f"data: [MODEL]{selected_model}\n\n"

            ollama_request = {
                "model": selected_model,
                "messages": conversation_history,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_gpu": OLLAMA_NUM_GPU,
                }
            }

            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_URL}/api/chat",
                    json=ollama_request,
                ) as response:
                    if response.status_code >= 400:
                        error_body = (await response.aread()).decode("utf-8", errors="replace")
                        try:
                            error_detail = json.loads(error_body).get("error", error_body)
                        except json.JSONDecodeError:
                            error_detail = error_body or f"Ollama error {response.status_code}"
                        yield f"data: [ERROR] {error_detail}\n\n"
                        return

                    line_iter = response.aiter_lines().__aiter__()
                    while True:
                        if is_stale_or_cancelled() or await request.is_disconnected():
                            cancelled = True
                            break

                        # Poll so Stop is noticed even while waiting on the next Ollama token
                        try:
                            line = await asyncio.wait_for(line_iter.__anext__(), timeout=0.25)
                        except asyncio.TimeoutError:
                            continue
                        except StopAsyncIteration:
                            break

                        if not line.strip():
                            continue

                        try:
                            chunk_data = json.loads(line)
                            message_data = chunk_data.get("message", {})
                            content_chunk = message_data.get("content") or ""
                            thinking_chunk = message_data.get("thinking") or ""

                            if thinking_chunk:
                                full_thinking += thinking_chunk
                                yield f"data: [THINK]{thinking_chunk}\n\n"
                            elif content_chunk:
                                if thinking_phase and full_thinking:
                                    thinking_phase = False
                                    yield f"data: [THINK_END]\n\n"
                                full_response += content_chunk
                                yield f"data: {content_chunk}\n\n"

                            if chunk_data.get("done", False):
                                break

                        except json.JSONDecodeError:
                            continue

                    if cancelled:
                        try:
                            await response.aclose()
                        except Exception:
                            pass

            if is_stale_or_cancelled() or await request.is_disconnected():
                cancelled = True
                yield "data: [CANCELLED]\n\n"
                return

            if full_response.strip() and not is_stale_or_cancelled():
                assistant_msg = ChatMessage(
                    session_id=session_id,
                    sender="assistant",
                    message=full_response,
                )
                db.add(assistant_msg)
                db.commit()

                message_count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()

                if message_count == 2 and (not session.title or session.title == "New Chat"):
                    user_first_message = msg.message

                    short_title = user_first_message.strip()[:40].strip()
                    if len(user_first_message) > 40:
                        short_title += "..."

                    db.execute(
                        ChatSession.__table__.update()
                        .where(ChatSession.id == session_id)
                        .values(title=short_title)
                    )
                    db.commit()

            yield f"data: [DONE]\n\n"

        except asyncio.CancelledError:
            cancelled = True
            raise
        except Exception as e:
            if not cancelled:
                yield f"data: [ERROR] {str(e)}\n\n"
        finally:
            if cancelled:
                try:
                    _remove_trailing_assistant_message(session_id, db)
                except Exception:
                    pass
            if _stream_generation_ids.get(session_id) == generation_id:
                _stream_generation_ids.pop(session_id, None)
            if _stream_cancel_events.get(session_id) is cancel_event:
                _stream_cancel_events.pop(session_id, None)
                

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/api/sessions/{session_id}/cancel")
async def cancel_stream(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop generation immediately. Keep the user message; drop incomplete assistant reply."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(404, "Conversation not found")

    if session_id in _stream_cancel_events:
        _stream_cancel_events[session_id].set()

    # Invalidate current generation so any in-flight stream refuses to save
    _stream_generation_ids.pop(session_id, None)
    _remove_trailing_assistant_message(session_id, db)

    return {"cancelled": True}


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

    db.delete(session)
    db.flush()
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


# Endpoint to list available Ollama models
@router.get("/api/ollama/models")
async def list_ollama_models():
    """Get list of available models from Ollama"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "Could not fetch models"}
    except Exception as e:
        return {"error": str(e)}


# New endpoint to get simplified available models for frontend
@router.get("/api/ollama/available-models")
async def get_available_models():
    """Get list of available models from Ollama (simplified for frontend)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                # Exclude CPU-only variants; show standard installed models
                models = [m for m in models if "cpu" not in m.lower()]
                return {"models": models}
            else:
                # Fallback to default list
                return {"models": AVAILABLE_MODELS}
    except Exception as e:
        # Return default models if Ollama is not reachable
        return {"models": AVAILABLE_MODELS, "error": str(e)}