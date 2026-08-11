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
import re
import time

from database import get_db, SessionLocal
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
# Force CPU by default: Quadro P1000 + newer Ollama CUDA builds hit PTX JIT / 0xc0000409.
# Set OLLAMA_NUM_GPU>0 only after updating NVIDIA drivers that can JIT the new kernels.
OLLAMA_NUM_GPU = int(os.getenv("OLLAMA_NUM_GPU", "0"))
# Cap context — qwen3 advertises 262k; on CPU that makes every token much slower.
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
OLLAMA_NUM_THREAD = int(
    os.getenv("OLLAMA_NUM_THREAD", str(max(4, (os.cpu_count() or 8) - 2)))
)
# Thinking + answer budget for Qwen (was 8192 — far too slow on CPU).
QWEN_NUM_PREDICT = int(os.getenv("QWEN_NUM_PREDICT", "1536"))
QWEN_HISTORY_MAX = int(os.getenv("QWEN_HISTORY_MAX", "20"))
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
# When Qwen dumps CoT into content (no native think), stop routing after this many chars
QWEN_MAX_CONTENT_COT_CHARS = 900
_CUDA_CRASH_HINTS = (
    "cuda error",
    "ptx jit",
    "0xc0000409",
    "llama-server process has terminated",
)

_stream_cancel_events: dict[int, asyncio.Event] = {}
_stream_generation_ids: dict[int, str] = {}
# Live Ollama HTTP handles so /cancel can hang up the stream immediately (stops CPU).
_active_ollama_streams: dict[int, dict] = {}
_installed_ollama_models: Optional[list[str]] = None
_installed_models_at: float = 0.0

# Only strip short canned intros like "I am Gemma (x)." — not real self-intros
_IDENTITY_PREFIX_RE = re.compile(
    r"^\s*I\s+am\s+(?:Gemma|Qwen)(?:\s*\([^)\n]{0,40}\))?\.\s+",
    re.IGNORECASE,
)
_PERSIAN_ARABIC_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
)
_LATIN_RE = re.compile(r"[A-Za-z]")
_PREFIX_BUFFER_MAX = 160
_COT_START_RE = re.compile(
    r"^\s*(okay,?\s+(?:let'?s\s+see|the\s+user)|let'?s\s+see|the\s+user\s+(?:is\s+asking|said)|"
    r"first,?\s+i\s+need|i\s+need\s+to\s+remember|looking\s+at\s+the\s+conversation|"
    r"so\s+the\s+user|the\s+conversation\s+history|hmm,?\s+|alright,?\s+|they\s+(?:asked|introduced|want))",
    re.IGNORECASE,
)
_COT_MARKERS_RE = re.compile(
    r"(?:^|\n)\s*(?:final\s+answer|answer\s*:|پاسخ\s*:)\s*",
    re.IGNORECASE,
)


def _model_identity(model_name: str) -> str:
    base = (model_name or OLLAMA_MODEL).split(":")[0].lower()
    if base.startswith("qwen3"):
        return "Qwen 3"
    if base.startswith("qwen"):
        return "Qwen"
    if base.startswith("gemma3"):
        return "Gemma 3"
    if base.startswith("gemma2"):
        return "Gemma 2"
    if base.startswith("gemma"):
        return "Gemma"
    return base or "Assistant"


def _is_qwen_model(model_name: str) -> bool:
    return (model_name or "").lower().startswith("qwen")


def _ollama_options(**extra) -> dict:
    """Build Ollama options; pin GPU/threads/ctx for stable, faster local runs."""
    opts = {
        "num_gpu": OLLAMA_NUM_GPU,
        "num_thread": OLLAMA_NUM_THREAD,
        "num_ctx": OLLAMA_NUM_CTX,
    }
    opts.update({k: v for k, v in extra.items() if v is not None})
    opts["num_gpu"] = OLLAMA_NUM_GPU
    return opts


def _qwen_stream_options() -> dict:
    """Faster defaults for Qwen on CPU: shorter output budget + capped context."""
    return _ollama_options(
        temperature=0.6,
        top_p=0.9,
        top_k=20,
        num_predict=QWEN_NUM_PREDICT,
    )


def _is_cuda_runner_crash(error_text: str) -> bool:
    lowered = (error_text or "").lower()
    return any(hint in lowered for hint in _CUDA_CRASH_HINTS)


async def _unload_ollama_model(model: str) -> None:
    """Drop a crashed GPU runner so the next request can load on CPU."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": model, "keep_alive": 0},
            )
    except Exception:
        pass


async def _abort_active_ollama_stream(session_id: int) -> None:
    """Hang up the in-flight Ollama HTTP stream so inference stops (like Ctrl+C)."""
    handles = _active_ollama_streams.pop(session_id, None)
    if not handles:
        return
    response = handles.get("response")
    client = handles.get("client")
    if response is not None:
        try:
            await response.aclose()
        except Exception:
            pass
    if client is not None:
        try:
            await client.aclose()
        except Exception:
            pass


def _register_ollama_stream(
    session_id: int,
    *,
    client: httpx.AsyncClient,
    response: Optional[httpx.Response] = None,
    model: str = "",
) -> None:
    _active_ollama_streams[session_id] = {
        "client": client,
        "response": response,
        "model": model,
    }


def _set_ollama_stream_response(
    session_id: int, response: Optional[httpx.Response]
) -> None:
    handles = _active_ollama_streams.get(session_id)
    if handles is not None:
        handles["response"] = response


async def _get_installed_ollama_models() -> list[str]:
    """Cached list of locally installed Ollama model tags."""
    global _installed_ollama_models, _installed_models_at
    now = time.monotonic()
    if _installed_ollama_models is not None and now - _installed_models_at < 60:
        return _installed_ollama_models
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                _installed_ollama_models = [
                    m["name"] for m in response.json().get("models", [])
                ]
                _installed_models_at = now
                return _installed_ollama_models
    except Exception:
        pass
    return _installed_ollama_models or []


async def _resolve_ollama_model(requested: str) -> str:
    """Use the requested Ollama tag when it is installed locally."""
    name = (requested or OLLAMA_MODEL).strip() or OLLAMA_MODEL
    models = await _get_installed_ollama_models()
    if not models:
        return name
    lowered = {m.lower(): m for m in models}
    return lowered.get(name.lower(), name)


def _encode_sse_chunk(text: str) -> str:
    """Escape newlines so answer/thinking chunks stay on one SSE data line."""
    return (text or "").replace("\n", "\\n")


async def _fetch_qwen_final_answer(
    client: httpx.AsyncClient,
    model: str,
    messages: list[dict[str, str]],
) -> tuple[str, str]:
    """Non-stream retry when think-mode streaming used the budget on reasoning only."""
    response = await client.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "think": True,
            "options": _ollama_options(temperature=0.6, num_predict=min(1024, QWEN_NUM_PREDICT)),
            "keep_alive": OLLAMA_KEEP_ALIVE,
        },
    )
    if response.status_code >= 400:
        return "", ""
    message = response.json().get("message", {})
    return (
        (message.get("thinking") or "").strip(),
        (message.get("content") or "").strip(),
    )


_REDACTED_OPEN = "<think>"
_REDACTED_CLOSE = "</think>"
_THINK_OPEN = "<think>"
_THINK_CLOSE = "</think>"
_TAG_SPECS = (
    (_REDACTED_OPEN, _REDACTED_CLOSE),
    (_THINK_OPEN, _THINK_CLOSE),
)
_REDACTED_BLOCK_RE = re.compile(
    r"<\s*(?:redacted_thinking|think)\s*>(.*?)<\s*/\s*(?:redacted_thinking|think)\s*>",
    re.IGNORECASE | re.DOTALL,
)


def _find_partial_tag_suffix(text: str, tag: str) -> int:
    """If `text` ends with a partial `tag` prefix, return index where suffix starts."""
    upper = min(len(text), len(tag) - 1)
    for size in range(upper, 0, -1):
        if text[-size:].lower() == tag[:size].lower():
            return len(text) - size
    return -1


class _RedactedThinkingSplitter:
    """Stream-safe splitter for <think>…</think> blocks."""

    def __init__(self) -> None:
        self._carry = ""
        self.thinking = ""
        self.answer = ""
        self._in_thinking = False
        self._close_tag = _REDACTED_CLOSE

    def push(self, chunk: str, *, flush: bool = False) -> tuple[str, str]:
        if chunk:
            self._carry += chunk
        self._drain(flush=flush)
        return self.thinking, self.answer

    def finish(self) -> tuple[str, str]:
        return self.push("", flush=True)

    def _drain(self, *, flush: bool) -> None:
        while self._carry:
            if not self._in_thinking:
                matched = False
                for open_tag, close_tag in _TAG_SPECS:
                    lower = self._carry.lower()
                    open_idx = lower.find(open_tag)
                    if open_idx >= 0:
                        self.answer += self._carry[:open_idx]
                        self._carry = self._carry[open_idx + len(open_tag) :]
                        self._in_thinking = True
                        self._close_tag = close_tag
                        matched = True
                        break
                    hold = _find_partial_tag_suffix(self._carry, open_tag)
                    if hold >= 0 and not flush:
                        self.answer += self._carry[:hold]
                        self._carry = self._carry[hold:]
                        matched = True
                        break
                if matched:
                    continue
                self.answer += self._carry
                self._carry = ""
                break

            close_tag = getattr(self, "_close_tag", _REDACTED_CLOSE)
            lower = self._carry.lower()
            close_idx = lower.find(close_tag)
            if close_idx >= 0:
                self.thinking += self._carry[:close_idx]
                self._carry = self._carry[close_idx + len(close_tag) :]
                self._in_thinking = False
                continue
            hold = _find_partial_tag_suffix(self._carry, close_tag)
            if hold >= 0 and not flush:
                self.thinking += self._carry[:hold]
                self._carry = self._carry[hold:]
                break
            if flush:
                self.thinking += self._carry
                self._carry = ""
                self._in_thinking = False
            else:
                self.thinking += self._carry
                self._carry = ""
            break


def _split_redacted_thinking(text: str) -> tuple[str, str]:
    """Return (thinking, answer) from a complete model string."""
    thinking_parts: list[str] = []

    def _collect(match: re.Match[str]) -> str:
        thinking_parts.append(match.group(1))
        return ""

    answer = _REDACTED_BLOCK_RE.sub(_collect, text or "")
    # Unclosed trailing block
    open_m = re.search(
        r"<\s*(?:redacted_thinking|think)\s*>(.*)$",
        answer,
        re.IGNORECASE | re.DOTALL,
    )
    if open_m:
        thinking_parts.append(open_m.group(1))
        answer = answer[: open_m.start()]
    return "".join(thinking_parts).strip(), answer.strip()


def _strip_instruction_leaks(text: str) -> str:
    """Remove bracket/meta instructions that leaked into the visible answer."""
    t = (text or "").strip()
    if not t:
        return t
    t = re.sub(
        r"\n*\[[^\]]*(?:فقط پاسخ|Reply with only|بدون استدلال|no reasoning)[^\]]*\]\s*$",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\n*\(لطفاً فقط[^\)]*\)\s*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\*?\s*But the instruction says[^*]*\*?", "", t, flags=re.IGNORECASE)
    t = re.sub(r"(?i):Me:|:\s*My response:", "", t)
    t = re.sub(r"\*+\s*$", "", t).strip()
    return t


def _strip_user_turn_suffixes(content: str) -> str:
    """Strip one-shot instruction suffixes before sending user turns back to the model."""
    t = (content or "").strip()
    t = re.sub(r"\n*\[[^\]]*(?:فقط|Reply with only|Reminder|یادآوری)[^\]]*\]\s*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\n*\(لطفاً فقط[^\)]*\)\s*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\n*\[Reminder:[^\]]*\]\s*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\n*\[یادآوری:[^\]]*\]\s*$", "", t, flags=re.IGNORECASE)
    return t.strip()


def _parse_model_output(raw: str) -> tuple[str, str]:
    """Split redacted_thinking tags and strip instruction leaks from the answer."""
    thinking, answer = _split_redacted_thinking(raw)
    return thinking.strip(), _strip_instruction_leaks(answer)


def _qwen_user_turn_suffix(user_content: str, prefer_persian: bool) -> str:
    """Extra instruction appended to the latest user turn for Qwen."""
    if not prefer_persian:
        return "\n\n[Reply with only the final answer — no reasoning or analysis.]"
    if _is_story_request(user_content):
        line_m = re.search(r"(\d+)\s*خط", user_content)
        n = line_m.group(1) if line_m else "3"
        return (
            f"\n\n[فقط داستان را به فارسی در {n} خط بنویس. "
            "بدون سلام یا مقدمه. بدون استدلال انگلیسی. جملات کامل.]"
        )
    if _is_continuation_request(user_content):
        return (
            "\n\n[ادامه داستان را به فارسی بنویس — "
            "۳ خط کامل. بدون سلام. بدون استدلال انگلیسی.]"
        )
    return "\n\n[فقط پاسخ نهایی را به فارسی بنویس. بدون استدلال یا تحلیل انگلیسی.]"


def _build_system_prompt(identity: str, prefer_persian: bool = False) -> str:
    lang = (
        "Reply in the same language as the user's latest message."
        if not prefer_persian
        else "The user writes in Persian — reply in natural Persian."
    )
    concise = ""
    if identity.lower().startswith("qwen"):
        concise = (
            "Keep internal reasoning brief and focused; "
            "then give a clear, useful answer without unnecessary length.\n"
        )
    return (
        f"You are {identity}, a helpful chat assistant.\n"
        "Use the conversation history in this session to answer follow-up questions.\n"
        "Remember what the user said earlier in this chat (name, previous messages, topics).\n"
        "When the user asks what they said or what you said, answer from this history.\n"
        f"{lang}\n"
        f"{concise}"
        "Put only the final user-facing reply in your answer — keep reasoning private."
    )


def get_conversation_history(
    session_id: int,
    db: Session,
    max_messages: int = 40,
    model_name: Optional[str] = None,
):
    """Build a plain user/assistant history for Ollama — no extra suffixes or thinking."""
    db.expire_all()

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )

    if len(messages) > max_messages:
        messages = messages[-max_messages:]

    identity = _model_identity((model_name or OLLAMA_MODEL).strip() or OLLAMA_MODEL)
    prefer_persian = False
    for m in reversed(messages):
        if m.sender == "user" and (m.message or "").strip():
            prefer_persian = _detect_reply_language(m.message) == "Persian"
            break

    history: list[dict[str, str]] = [
        {
            "role": "system",
            "content": _build_system_prompt(identity, prefer_persian=prefer_persian),
        }
    ]

    last_role: Optional[str] = None
    for msg in messages:
        raw = (msg.message or "").strip()
        if not raw:
            continue

        if msg.sender == "user":
            content, _ = _strip_reply_markers(raw)
            content = content.strip()
            role = "user"
        else:
            content = _sanitize_assistant_content(raw)
            role = "assistant"

        if not content:
            continue

        if last_role == role and history and history[-1]["role"] == role:
            history[-1]["content"] += "\n\n" + content
            continue

        history.append({"role": role, "content": content})
        last_role = role

    return history


def _detect_reply_language(text: str) -> Optional[str]:
    """Return 'Persian' when Persian/Arabic script dominates the user text."""
    if not text:
        return None
    sample = re.sub(r"<<<.*?>>>", " ", text, flags=re.DOTALL)
    sample = re.sub(
        r"\[یادآوری:.*?\]|\[Reminder:.*?\]",
        " ",
        sample,
        flags=re.IGNORECASE | re.DOTALL,
    )
    persian = len(_PERSIAN_ARABIC_RE.findall(sample))
    latin = len(_LATIN_RE.findall(sample))
    if persian == 0:
        return None
    if persian >= max(latin, 1):
        return "Persian"
    return None


def _is_qwen_instruction_leak(text: str) -> bool:
    """Detect Qwen meta/instruction text that leaked into the answer bubble."""
    t = (text or "").strip()
    if not t:
        return False
    return bool(
        re.search(
            r"(?i)(just the answer|they need to read|only the final answer|"
            r"I should introduce myself|instruction says|no reasoning|"
            r"reply with only|let me check the instructions|"
            r"I need to respond|I need to reply|so I should)",
            t,
        )
    )


def _is_qwen_cot_fragment(text: str) -> bool:
    """Detect partial CoT debris that is not a user-facing reply."""
    t = (text or "").strip()
    if not t:
        return True
    if _is_qwen_instruction_leak(t) or _looks_like_chain_of_thought(t):
        return True
    # Starts mid-sentence: ", and I responded with"
    if re.match(r"^[,.\-–—:;]\s*\w", t):
        return True
    if re.match(r"(?i)^(so,|and I|but I|which means|I responded with|they said)", t):
        return True
    if re.search(
        r"(?i)\b(I responded with|responded with|the user first|first said|"
        r"so the user|the answer is that they|best response is)\b",
        t,
    ):
        return True
    # Short clause with no sentence ending — not a real answer
    if (
        len(t) < 50
        and not re.search(r"[.!?…؟]['\"»)]?\s*$", t)
        and re.search(r"(?i)\b(and|with|that|said|responded|the user|they)\b", t)
    ):
        return True
    return False


def _looks_like_chain_of_thought(text: str) -> bool:
    """Detect English meta-reasoning that Qwen sometimes dumps as the answer."""
    t = (text or "").strip()
    if not t:
        return False
    if _is_qwen_instruction_leak(t):
        return True
    if _COT_START_RE.match(t):
        return True
    if re.match(r"(?is)^\s*(yes[,.]?\s*)?(so[,.]?\s*)?(the\s+)?(final\s+)?answer\s+is\b", t):
        return True
    latin = len(_LATIN_RE.findall(t))
    if latin >= 40 and re.search(
        r"(?i)\b("
        r"user (?:is asking|said|wrote|introduced|asked)|"
        r"they (?:asked|introduced|want|said)|"
        r"which means|in persian|conversation history|"
        r"assistant (?:responded|replied)|I need to|response (?:should|in)|"
        r"naturally\.?\s*$"
        r")\b",
        t,
    ):
        return True
    persian = len(_PERSIAN_ARABIC_RE.findall(t))
    if latin > 80 and persian < 8 and re.search(
        r"\b(user is asking|conversation history|assistant (responded|replied)|I need to)\b",
        t,
        re.IGNORECASE,
    ):
        return True
    return False


def _is_english_meta_dump(text: str) -> bool:
    """English reasoning that quotes Persian words is still not a user-facing answer."""
    t = (text or "").strip()
    if not t:
        return False
    if _is_qwen_instruction_leak(t):
        return True
    latin = len(_LATIN_RE.findall(t))
    if latin < 25:
        return False
    if _looks_like_chain_of_thought(t):
        return True
    if latin > 30 and not _is_mostly_persian(t) and re.search(
        r"(?i)\b(okay|the user|they (?:said|asked)|which means|in persian)\b",
        t,
    ):
        return True
    return False


def _is_english_chunk(chunk: str, persian_answer_started: bool = False) -> bool:
    """Detect English meta-reasoning fragments — not normal English answers."""
    t = (chunk or "").strip()
    if not t:
        return False
    if re.search(
        r"(?i)\b(wait|okay|let me|the user|which means|second line|first line|maybe|"
        r"the user|i need to|looking at|conversation history|they asked|"
        r"superposition|entanglement|in persian)\b",
        t,
    ):
        return True
    if persian_answer_started:
        latin = len(_LATIN_RE.findall(t))
        persian = len(_PERSIAN_ARABIC_RE.findall(t))
        if latin >= 4 and latin > persian:
            return True
    return False


def _clean_persian_only(text: str) -> str:
    """Strip English meta-reasoning; keep only Persian user-facing content."""
    if not text:
        return ""

    lines = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        persian = len(_PERSIAN_ARABIC_RE.findall(line))
        latin = len(_LATIN_RE.findall(line))
        if persian >= 3 and persian > latin:
            if not _looks_like_chain_of_thought(line) and not _is_english_meta_dump(line):
                lines.append(line)
                continue
        cleaned = re.sub(
            r"(?i)(?:^|\s)(?:okay|wait|let me|second line|first line|maybe|"
            r"the user|which means|in persian|i need to|check some|user wants|"
            r"superposition|entanglement)[^.!?؟\n]*[.!?]?\s*",
            " ",
            line,
        )
        cleaned = re.sub(r"[A-Za-z][A-Za-z0-9\s,\':\-\(\)]*", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-")
        if len(_PERSIAN_ARABIC_RE.findall(cleaned)) >= 3:
            lines.append(cleaned)

    if lines:
        return "\n".join(lines).strip()

    segments = re.findall(
        r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\s،؛؟!.,\-«»\"'0-9]+",
        text,
    )
    segments = [
        s.strip()
        for s in segments
        if len(_PERSIAN_ARABIC_RE.findall(s)) >= 8
    ]
    return "\n".join(segments[:4]).strip() if segments else ""


def _chunk_should_go_to_thinking(
    chunk: str,
    accumulator: str,
    prefer_persian: bool,
    persian_answer_started: bool,
    is_qwen: bool = False,
    answer_started: bool = False,
) -> bool:
    """Route CoT / meta-reasoning into the thinking bubble, not the answer."""
    if answer_started:
        # Still peel off late meta fragments after a real answer began
        if _is_english_chunk(chunk, persian_answer_started or answer_started):
            return True
        return False

    if _looks_like_chain_of_thought(accumulator) or _is_english_meta_dump(accumulator):
        return True
    if _is_english_chunk(chunk, persian_answer_started):
        return True
    if is_qwen:
        latin = len(_LATIN_RE.findall(accumulator))
        persian = len(_PERSIAN_ARABIC_RE.findall(accumulator))
        # Do NOT match bare "I'm" / "I am" — those start normal answers ("I'm Qwen3...")
        if latin >= 12 and latin > persian and re.search(
            r"(?i)\b(let me|okay|ok[,.]|the user|i need to|they asked|"
            r"looking at|conversation history|wait[,.]|so the answer|"
            r"i should (?:say|respond|clarify|retell)|my response|final answer|"
            r"in persian|which means|reasoning)\b",
            accumulator[:320],
        ):
            return True
        if latin >= 24 and latin > persian * 2 and re.search(
            r"(?i)\b(the user|conversation history|i need to|looking at|"
            r"should (?:say|respond)|chain of thought)\b",
            accumulator[:400],
        ):
            return True
    if prefer_persian and not _is_mostly_persian(chunk) and not persian_answer_started:
        return True
    return False


def _unwrap_meta_answer(text: str) -> str:
    """
    Turn meta wrappers into the real reply.
    e.g. Yes, so the answer is "سلام محمد!" -> سلام محمد!
    """
    t = (text or "").strip()
    if not t:
        return t

    quoted = re.search(
        r'(?is)(?:final\s+)?answer\s+is\s*[:\-]?\s*[«"\']([^"\'»]+)[»"\']',
        t,
    )
    if quoted:
        return quoted.group(1).strip()

    stripped = re.sub(
        r'(?is)^\s*(yes[,.]?\s*)?(so[,.]?\s*)?(the\s+)?(final\s+)?answer\s+is\s*[:\-]?\s*',
        "",
        t,
    ).strip().strip("«»\"'")
    if stripped and stripped != t:
        return stripped

    return t


def _persian_lines(text: str) -> list[str]:
    """Return lines that are predominantly Persian (not English with a Persian quote)."""
    lines = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or not _PERSIAN_ARABIC_RE.search(line):
            continue
        persian = len(_PERSIAN_ARABIC_RE.findall(line))
        latin = len(_LATIN_RE.findall(line))
        if persian >= 3 and persian > latin:
            lines.append(line)
    return lines


_NAME_FROM_USER_RE = re.compile(
    r"(?:اسم\s*(?:من|م)\s+)?(?:من\s+)?([^\s،,.\n!?؟]{2,20})\s+هست(?:م|ش|)",
)
_NAME_EXPLICIT_RE = re.compile(
    r"اسم\s*(?:من|م)\s+([^\s،,.\n!?؟]{2,20})",
)
_NAME_EN_RE = re.compile(
    r"(?i)\b(?:my name(?:'s| is)|i am|i'm|call me)\s+([A-Za-z][\w'-]{1,18})\b",
)
_NAME_EN_SAID_RE = re.compile(
    r"(?i)\b(?:i said|i told you)[^.!?]{0,60}\b(?:my name is|i am|i'm)\s+([A-Za-z][\w'-]{1,18})\b",
)
_NAME_SKIP = {
    "ki", "what", "who", "the", "my", "is", "am", "me", "hi", "hello", "hey",
    "yes", "no", "ok", "okay", "well", "so", "and", "but", "that", "this",
    "کی", "چی", "چه", "کیه", "چیست", "هستم", "هست", "سلام", "من",
}


def _normalize_inferred_name(name: str) -> str:
    name = (name or "").strip().strip("«»\"'")
    if not name or name.lower() in _NAME_SKIP:
        return ""
    if name.isascii():
        return name[0].upper() + name[1:].lower()
    return name


def _infer_user_name_from_texts(texts: list[str]) -> Optional[str]:
    """Best-effort extract of the user's name from session messages (newest first)."""
    for text in reversed(texts):
        if not text:
            continue
        for pat in (
            _NAME_EN_SAID_RE,
            _NAME_EN_RE,
            _NAME_EXPLICIT_RE,
            _NAME_FROM_USER_RE,
        ):
            m = pat.search(text)
            if not m:
                continue
            name = _normalize_inferred_name(m.group(1))
            if name:
                return name
    return None


def _is_mostly_persian(text: str) -> bool:
    t = text or ""
    persian = len(_PERSIAN_ARABIC_RE.findall(t))
    latin = len(_LATIN_RE.findall(t))
    return persian >= 3 and persian > latin


def _infer_session_answer(
    user_message: str,
    history_texts: list[str],
    identity: str,
    prefer_persian: bool,
    user_only_texts: Optional[list[str]] = None,
) -> Optional[str]:
    """
    When the model dumps CoT / empty content, answer common follow-ups
    from this session's history so the user still gets a natural reply.
    """
    q = (user_message or "").strip()
    q_compact = re.sub(r"\s+", " ", q)

    def _strip_reminder(t: str) -> str:
        t = re.sub(r"\n*\(لطفاً فقط به فارسی.*?\)\s*$", "", t, flags=re.DOTALL)
        t = re.sub(r"\n*\[یادآوری:.*?\]\s*$", "", t, flags=re.DOTALL)
        t = re.sub(r"\n*\[Reminder:.*?\]\s*$", "", t, flags=re.DOTALL)
        t = re.sub(r"\n*\[Reply with only.*?\]\s*$", "", t, flags=re.DOTALL)
        t = re.sub(r"\n*\[فقط .*?\]\s*$", "", t, flags=re.DOTALL)
        return t.strip()

    source_users = user_only_texts if user_only_texts is not None else history_texts
    prior_users = []
    for t in source_users:
        cleaned = _strip_reminder(t or "")
        if cleaned and cleaned != q.strip():
            prior_users.append(cleaned)

    # Greeting / name introduction
    if re.search(r"(سلام|hello|hi\b|hey\b)", q_compact, re.IGNORECASE):
        name = _infer_user_name_from_texts([q] + prior_users)
        if name and prefer_persian:
            return f"سلام {name}! خوشحالم از آشنایی با شما. چطور می‌تونم کمک کنم؟"
        if prefer_persian:
            return "سلام! خوشحالم از آشنایی با شما. چطور می‌تونم کمک کنم؟"
        if name:
            return f"Hello {name}! I'm doing well — how can I help you today?"
        if re.search(r"(?i)\bhow (?:are|you doing|r you)\b", q_compact):
            return "Hello! I'm doing well, how can I help you today?"
        return "Hello! How can I help you today?"

    asking_who = any(
        s in q_compact for s in ("کی هستی", "تو کی", "who are you", "خودت کی")
    )
    if asking_who:
        return (
            f"من {identity} هستم، دستیار هوشمند شما. چطور می‌تونم کمک کنم؟"
            if prefer_persian
            else f"I'm {identity}, your helpful AI assistant."
        )

    asking_age = bool(
        re.search(
            r"(?i)\b(how old (?:are|r) you|what(?:'s| is) your age|your age)\b",
            q_compact,
        )
        or re.search(r"(چند سالته|سنت چنده|چند سال داری)", q_compact)
    )
    if asking_age:
        return (
            f"من سن انسانی ندارم — یک مدل زبانی به اسم {identity} هستم. چطور می‌تونم کمک کنم؟"
            if prefer_persian
            else f"I don't have a human age — I'm {identity}, an AI language model. How can I help?"
        )

    asking_name = any(
        s in q_compact
        for s in (
            "اسم من چی", "اسمم چی", "اسم من چه", "من کی بودم",
            "what was my name", "what's my name", "what is my name",
        )
    )
    if asking_name:
        name = _infer_user_name_from_texts(prior_users + [q])
        if name:
            return f"اسم شما {name} است." if prefer_persian else f"Your name is {name}."
        return (
            "هنوز اسم‌تان را در این گفتگو نگفته‌اید."
            if prefer_persian
            else "You haven't told me your name in this chat yet."
        )

    # User introducing or reminding about their name
    name_related = bool(
        re.search(
            r"(?i)\b(my name is|i'?m|i am|call me|i said my name|i told you my name|"
            r"you forgot|remember my name)\b",
            q_compact,
        )
        or re.search(r"اسم\s*من", q_compact)
    )
    if name_related:
        name = _infer_user_name_from_texts(prior_users + [q])
        if name:
            if prefer_persian:
                return f"بله، اسم شما {name} است. چطور می‌تونم کمک کنم؟"
            return f"You're right — your name is {name}. How can I help you?"
        if prefer_persian:
            return "متوجه شدم. لطفاً اسم‌تان را دوباره بگویید."
        return "Got it — could you tell me your name again?"

    asking_prev = bool(
        re.search(
            r"(?i)(سوال قبل|سوال قبلی|قبلی چی پرسید|چی پرسیدم|من چی گفتم|چی گفتم|"
            r"what did i ask|what did i say|what was my message|what did i tell you|"
            r"previous question|my last message|پیام قبلی|در پیام قبلی|گفتم چی)",
            q_compact,
        )
    )
    if asking_prev and prior_users:
        prev = prior_users[-1]
        if re.search(
            r"(?i)what did i say|what was my message|what did i tell you|my last message|"
            r"چی گفتم|گفتم چی|پیام قبلی|در پیام قبلی",
            q_compact,
        ):
            return (
                f'شما گفتید: «{prev}»'
                if prefer_persian
                else f'You said "{prev}".'
            )
        return (
            f"سوال قبلی‌تان این بود: «{prev}»"
            if prefer_persian
            else f'Your previous question was: "{prev}"'
        )

    # Retell / repeat — NOT new story requests ("یک داستان بگو")
    asking_retell = bool(
        re.search(
            r"(?i)\b(yes what|what(?:'s| is)?(?:\s+the)?\s+story|tell(?:\s+it|\s+me)?\s+again|"
            r"repeat(?:\s+the)?\s+story|retell|say(?:\s+it)?\s+again|what did you (?:tell|say))\b",
            q_compact,
        )
        or re.search(
            r"(دوباره بگو|چی گفتی|چیزی که گفتی|همون(?: داستان)?|همونو بگو|تکرار کن)",
            q_compact,
        )
    )
    if asking_retell and not _is_story_request(q):
        for t in reversed(history_texts):
            cleaned = _strip_reminder(t or "")
            if (
                cleaned
                and not _is_trivial_answer(cleaned)
                and not _is_generic_fallback(cleaned)
                and not _looks_like_chain_of_thought(cleaned)
                and len(cleaned) > 40
                and cleaned != q.strip()
            ):
                # Prefer prior assistant-style content (stories, explanations)
                if cleaned not in prior_users:
                    return cleaned
        # Fall back to longest prior user-context reply-like blob already in history
        candidates = [
            _strip_reminder(t)
            for t in history_texts
            if t and len(_strip_reminder(t)) > 60
        ]
        if candidates:
            return max(candidates, key=len)

    return None


def _is_generic_fallback(text: str) -> bool:
    t = (text or "").strip()
    return "پاسخ واضحی ساخته نشد" in t or t == "I couldn't form a clear answer. Please ask again."


def _is_continuation_request(text: str) -> bool:
    t = (text or "").strip()
    return bool(
        re.search(
            r"(در ادامه|ادامه(?:\s+بده|\s+چی)|بعدش چی|بعد(?:اً)?\s+چی|what(?:'s| is)? next|"
            r"what happens next|continue|go on)",
            t,
            re.IGNORECASE,
        )
    )


def _qwen_route_chunk(
    chunk: str,
    accumulator: str,
    prefer_persian: bool,
    answer_started: bool,
) -> str:
    """Return 'think' or 'answer' for a Qwen content chunk."""
    if not chunk:
        return "think"
    if answer_started:
        if _is_english_chunk(chunk, True):
            return "think"
        return "answer"
    if _is_english_chunk(chunk, False) or _COT_START_RE.match(accumulator.strip()):
        return "think"
    if _looks_like_chain_of_thought(accumulator) or _is_english_meta_dump(accumulator):
        return "think"
    if prefer_persian:
        if _PERSIAN_ARABIC_RE.search(chunk):
            return "answer"
        return "think"
    # English chat: real reply once past meta intro
    latin = len(_LATIN_RE.findall(accumulator))
    if latin >= 8 and not re.search(
        r"(?i)\b(the user|okay|let me|i need to|looking at)\b",
        accumulator[:200],
    ):
        return "answer"
    return "think"


def _finalize_qwen_answer(
    full_response: str,
    full_thinking: str,
    content_accumulator: str,
    *,
    identity: str,
    prefer_persian: bool,
    user_message: str,
    history_all_texts: list[str],
    history_user_texts: Optional[list[str]] = None,
) -> str:
    """Pick the best Qwen user-facing answer without mangling a good stream."""
    routed = (full_response or "").strip()
    raw = (content_accumulator or "").strip()

    best = routed
    if not best and raw and not _looks_like_chain_of_thought(raw):
        best = raw

    if prefer_persian and best:
        cleaned = _clean_persian_only(best)
        if cleaned and len(cleaned) >= max(len(best) * 0.6, 8):
            best = cleaned

    # Always try to promote a declared reply from thinking when content is empty / CoT
    if (
        not best
        or _is_trivial_answer(best)
        or _looks_like_chain_of_thought(best)
        or _is_qwen_instruction_leak(best)
        or _is_qwen_cot_fragment(best)
        or _is_english_meta_dump(best)
        or _answer_fails_user_request(best, user_message)
        or (prefer_persian and not _is_mostly_persian(best))
    ):
        declared = _pull_declared_answer_from_thinking(
            full_thinking, prefer_persian=prefer_persian
        )
        if declared and not _answer_fails_user_request(declared, user_message):
            best = declared
        else:
            extracted = _extract_persian_answer("", full_thinking, user_message)
            if not extracted and full_thinking:
                extracted = _extract_english_answer_from_thinking(full_thinking)
            if extracted and not _answer_fails_user_request(extracted, user_message):
                if not best or len(extracted) > len(best):
                    best = extracted

    if (
        not best
        or _is_trivial_answer(best)
        or _answer_fails_user_request(best, user_message)
        or _is_qwen_cot_fragment(best)
    ) and not _is_story_request(user_message):
        inferred = _infer_session_answer(
            user_message, history_all_texts, identity, prefer_persian, history_user_texts
        )
        if inferred and not _is_trivial_answer(inferred):
            best = inferred

    return (best or "").strip()


def _is_story_request(text: str) -> bool:
    t = (text or "").strip()
    return bool(re.search(r"(داستان|story)", t, re.IGNORECASE))


def _is_greeting_persian(text: str) -> bool:
    t = (text or "").strip()
    return bool(
        re.search(
            r"(خوشحالم|چطور می‌تونم|چطور می‌توانم|سلام\s|از آشنایی)",
            t,
        )
    )


def _extract_persian_story_from_thinking(thinking: str, user_message: str = "") -> str:
    """Pull a Persian story draft from Qwen's thinking trace."""
    t = (thinking or "").strip()
    if not t:
        return ""

    n_lines = 3
    m = re.search(r"(\d+)\s*خط", user_message or "")
    if m:
        n_lines = min(max(int(m.group(1)), 1), 10)

    candidates: list[str] = []

    # Quoted Persian drafts in thinking
    for span in re.findall(r'[«"\']([^"\']{15,800})[»"\']', t):
        span = span.strip()
        if (
            _is_mostly_persian(span)
            and not _looks_like_chain_of_thought(span)
            and not _is_greeting_persian(span)
        ):
            candidates.append(span)

    # Persian lines (skip meta / greeting)
    persian_lines: list[str] = []
    for line in t.splitlines():
        line = line.strip()
        if not line or not _PERSIAN_ARABIC_RE.search(line):
            continue
        if (
            _looks_like_chain_of_thought(line)
            or _is_english_meta_dump(line)
            or _is_greeting_persian(line)
        ):
            continue
        if len(_PERSIAN_ARABIC_RE.findall(line)) >= 6:
            persian_lines.append(line)

    if persian_lines:
        block = "\n".join(persian_lines[-n_lines:]).strip()
        if block and not _is_greeting_persian(block):
            candidates.append(block)

    if not candidates:
        return ""

    # Prefer longest non-greeting candidate
    best = max(candidates, key=len)
    lines = [ln.strip() for ln in best.splitlines() if ln.strip()]
    if len(lines) > n_lines:
        lines = lines[-n_lines:]
    return "\n".join(lines).strip()


def _answer_fails_user_request(finalized: str, user_message: str) -> bool:
    """True when the reply clearly doesn't match what the user asked."""
    ans = (finalized or "").strip()
    q = (user_message or "").strip()
    if not ans or not q:
        return True
    if _is_story_request(q) or _is_continuation_request(q):
        if _is_greeting_persian(ans) or re.search(r"چطور می‌تونم کمک", ans):
            return True
        if len(ans) < 30 or _answer_looks_incomplete(ans):
            return True
    return False


def _pull_declared_answer_from_thinking(thinking: str, prefer_persian: bool = False) -> str:
    """
    Qwen often writes the real reply inside thinking as:
      So the response should be: سلام! من خوب هستم، شما چطور؟
    without quotes. Pull that user-facing text out.
    """
    t = (thinking or "").strip()
    if not t:
        return ""

    marker_re = re.compile(
        r"(?is)(?:^|\n|[.!?]\s+)"
        r"(?:so[, ]+)?(?:the\s+)?"
        r"(?:final\s+)?"
        r"(?:response|reply|answer)\s+"
        r"(?:should\s+be|is|will\s+be)\s*[:\-]?\s*"
    )
    matches = list(marker_re.finditer(t))
    if not matches:
        # Also catch mid-line without sentence start
        marker_re = re.compile(
            r"(?is)\b(?:so[, ]+)?(?:the\s+)?"
            r"(?:final\s+)?"
            r"(?:response|reply|answer)\s+"
            r"(?:should\s+be|is)\s*[:\-]?\s*"
        )
        matches = list(marker_re.finditer(t))
    if not matches:
        return ""

    candidates: list[str] = []
    for m in matches:
        rest = t[m.end() :]
        # Stop at next meta declaration / English self-talk
        rest = re.split(
            r"(?is)\s+(?:So[, ]+(?:the\s+)?(?:response|reply|answer)\s+(?:should\s+be|is)\b|"
            r"(?:Okay|Wait|Hmm|Alright|Let me|I (?:should|need|will|think)|The user)\b)",
            rest,
            maxsplit=1,
        )[0]
        ans = rest.strip().strip("«»\"'“”").strip()
        # Drop trailing English meta on the same fragment
        ans = re.split(
            r"(?is)\s+(?:So the (?:response|answer)|Okay|Wait|I need|The user)\b",
            ans,
            maxsplit=1,
        )[0].strip()
        if not ans or _is_trivial_answer(ans):
            continue
        if _looks_like_chain_of_thought(ans) and not _PERSIAN_ARABIC_RE.search(ans):
            continue
        # Mixed English+Persian line → keep Persian only when preferred
        if prefer_persian and _PERSIAN_ARABIC_RE.search(ans):
            persian_only = _clean_persian_only(ans)
            if persian_only:
                ans = persian_only
            else:
                # Grab contiguous Persian spans from the fragment
                spans = re.findall(
                    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\s،؛؟!.,\-«»\"'0-9!]+",
                    ans,
                )
                spans = [s.strip(" ,.-") for s in spans if len(_PERSIAN_ARABIC_RE.findall(s)) >= 4]
                if spans:
                    ans = " ".join(spans).strip()
        if ans and not _is_qwen_instruction_leak(ans):
            candidates.append(ans)

    if not candidates:
        return ""
    # Prefer the longest non-meta candidate (usually the last draft)
    return max(candidates, key=len).strip()


def _extract_persian_answer(text: str, thinking: str = "", user_message: str = "") -> str:
    """Pull a Persian user-facing answer from model output or its thinking trace."""
    prefer_persian = _detect_reply_language(user_message) == "Persian"
    user_is_greeting = bool(
        re.search(r"(?i)(سلام|hello|hi\b|hey\b|چطوری|چطورید)", user_message or "")
    )

    # Highest-signal: "response should be: …" drafts inside thinking
    for source in (thinking, text):
        declared = _pull_declared_answer_from_thinking(source or "", prefer_persian=True)
        if declared and _is_mostly_persian(declared):
            if user_is_greeting or not _is_greeting_persian(declared) or len(declared) > 25:
                return declared

    if thinking and (_is_story_request(user_message) or _is_continuation_request(user_message)):
        story = _extract_persian_story_from_thinking(thinking, user_message)
        if story:
            return story

    for source in (text, thinking):
        if not source:
            continue
        parts = _COT_MARKERS_RE.split(source)
        for part in reversed(parts):
            part = _unwrap_meta_answer(part.strip())
            if (
                part
                and _is_mostly_persian(part)
                and not _is_english_meta_dump(part)
                and not _looks_like_chain_of_thought(part)
                and (user_is_greeting or not _is_greeting_persian(part))
            ):
                return part.strip()
        # Whole-line Persian (skip greeting filters when user greeted)
        persian_chunks = []
        for ln in _persian_lines(source):
            if user_is_greeting or not _is_greeting_persian(ln):
                persian_chunks.append(ln)
        if persian_chunks:
            return "\n".join(persian_chunks[-4:]).strip()
        # Mixed English/Persian lines — pull Persian spans
        cleaned = _clean_persian_only(source)
        if cleaned and (user_is_greeting or not _is_greeting_persian(cleaned)):
            return cleaned
    return ""


def _is_trivial_answer(text: str) -> bool:
    """Punctuation / one-word stubs that are not real replies."""
    t = (text or "").strip()
    if not t:
        return True
    # Only punctuation / symbols
    if re.fullmatch(r"[\W_]+", t, flags=re.UNICODE):
        return True
    # Very short acknowledgements that are useless alone
    if re.fullmatch(
        r"(?i)(yes|no|ok|okay|sure|yep|yeah|nope|hi|hello|hey)\.?",
        t,
    ):
        return True
    if len(t) <= 2:
        return True
    return False


def _extract_english_answer_from_thinking(thinking: str) -> str:
    """Pull a user-facing English answer from Qwen's thinking trace."""
    t = (thinking or "").strip()
    if not t:
        return ""

    def _ok(ans: str) -> bool:
        ans = _unwrap_meta_answer((ans or "").strip())
        if not ans or _is_trivial_answer(ans):
            return False
        if len(ans) > 2500:
            return False
        if _looks_like_chain_of_thought(ans) or _is_english_meta_dump(ans):
            return False
        if _is_qwen_cot_fragment(ans):
            return False
        return True

    # History recall from thinking: "they said 'hello'"
    recall = re.search(
        r"(?is)(?:answer is(?: that)?|(?:the user|they))\s+(?:first\s+)?said\s+"
        r"[\"']([^\"']{1,300})[\"']",
        t,
    )
    if recall:
        said = recall.group(1).strip()
        ans = f'You said "{said}".' if said else ""
        if _ok(ans):
            return ans

    recall2 = re.search(
        r"(?is)the answer is that (?:the user|they) said ['\"]([^'\"]+)['\"]",
        t,
    )
    if recall2:
        ans = f'You said "{recall2.group(1).strip()}".'
        if _ok(ans):
            return ans

    recall3 = re.search(
        r"(?is)the answer is that (?:the user|they) said (\w+)",
        t,
    )
    if recall3:
        ans = f'You said "{recall3.group(1).strip()}".'
        if _ok(ans):
            return ans

    # Separate " and ' patterns so apostrophes inside "I'm" don't truncate
    quote_pairs = [
        ('"', '"'),
        ("'", "'"),
        ("«", "»"),
        ("“", "”"),
    ]
    lead_ins = [
        r"so(?:[, ]+the)?\s+answer\s+is",
        r"(?:final\s+)?answer\s+is",
        r"(?:response|reply)\s+should\s+be",
        r"(?:so[, ]+)?(?:the\s+)?response\s+is",
        r"I(?:\'ll| will)\s+(?:say|respond|reply|retell|repeat)",
        r"(?:here(?:'s| is)(?:\s+the)?(?:\s+story)?|the story (?:was|is|goes))",
        r"(?:maybe|perhaps)",
    ]
    for lead in lead_ins:
        for open_q, close_q in quote_pairs:
            pat = (
                rf'(?is){lead}\s*[:\-]?\s*{re.escape(open_q)}'
                rf'([^{re.escape(close_q)}]{{2,2500}}){re.escape(close_q)}'
            )
            matches = list(re.finditer(pat, t))
            if not matches:
                continue
            ans = matches[-1].group(1).strip()
            if _ok(ans):
                return _unwrap_meta_answer(ans)

    # Unquoted "response should be: ..." / "response is: ..."
    declared = _pull_declared_answer_from_thinking(t, prefer_persian=False)
    if declared and _ok(declared):
        return declared

    # Multi-line block after "answer is" / "response is" / "story is" (unquoted)
    bare = re.search(
        r'(?is)(?:so(?:[, ]+the)?\s+(?:answer|response)\s+is|'
        r'(?:response|reply)\s+should\s+be|'
        r'here(?:\'s| is)(?:\s+the)?(?:\s+story)?|'
        r'the story (?:was|is|goes)|I(?:\'ll| will)\s+(?:say|retell|repeat))\s*[:\-]?\s*(.+)$',
        t,
    )
    if bare:
        ans = _unwrap_meta_answer(bare.group(1).strip().strip("«»\"'“”"))
        # Drop trailing meta self-talk after the reply
        ans = re.split(
            r'(?is)\n(?:okay|wait|so I|I think|no need|the user|looking at)\b',
            ans,
            maxsplit=1,
        )[0].strip()
        sentences = re.split(r'(?<=[.!?])\s+', ans)
        kept: list[str] = []
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if _looks_like_chain_of_thought(s) or _is_english_meta_dump(s):
                if kept:
                    break
                continue
            kept.append(s)
            if len(" ".join(kept)) > 1200:
                break
        ans = " ".join(kept).strip()
        if _ok(ans):
            return ans

    # Last resort: longest quoted span that looks like a real reply (story / greeting)
    quoted_spans = re.findall(r'"([^"\n]{20,2500})"', t)
    quoted_spans += re.findall(r"'([^'\n]{20,2500})'", t)
    best = ""
    for span in quoted_spans:
        span = span.strip()
        if _ok(span) and len(span) > len(best):
            best = span
    if best:
        return best

    return ""


def _answer_looks_incomplete(text: str) -> bool:
    """True when the reply was cut off mid-sentence / mid-word (token budget, etc.)."""
    t = (text or "").strip()
    if not t:
        return True
    if _is_trivial_answer(t):
        return True
    # Persian/Arabic: ends mid-word (single short token, no sentence end)
    if _PERSIAN_ARABIC_RE.search(t):
        words = t.split()
        last_token = words[-1] if words else t
        if (
            len(last_token) <= 2
            and not re.search(r'[.!?…؟]$', t)
            and len(t) < 120
        ):
            return True
        if t.endswith("،") or t.endswith(","):
            return True
    # Clear sentence end → treat as complete
    if re.search(r'[.!?…؟😂😊🙏✨]$', t) or re.search(r'[.!?…؟]["\'»)”]\s*$', t):
        return False
    # Short acknowledgements without period can still be complete
    if len(t) < 48 and not re.search(
        r"(?i)\b(i|i'm|and|or|but|the|a|an|to|for|with|because|don|woul|shoul|hav)$",
        t,
    ):
        return False
    # Ends with a dangling function word / truncated token
    if re.search(
        r"(?i)\b(i|i'm|i'm|and|or|but|the|a|an|to|for|with|because|becaus|"
        r"don|woul|shoul|hav|wha|tha|thi|yo)$",
        t,
    ):
        return True
    # Longer text with no terminal punctuation → likely truncated
    if len(t) >= 48 and not re.search(r'[.!?…؟]$', t):
        return True
    return False


def _answer_looks_like_stub(answer: str, thinking: str = "") -> bool:
    """True when streamed content is a truncated stub and thinking has the real reply."""
    a = (answer or "").strip()
    if not a or _is_trivial_answer(a):
        return True
    if _is_generic_fallback(a) or _looks_like_chain_of_thought(a) or _is_english_meta_dump(a):
        return True
    if _is_qwen_cot_fragment(a):
        return True
    if _answer_looks_incomplete(a):
        return True

    thinking = (thinking or "").strip()
    if not thinking or len(thinking) < 80:
        return False

    # Only treat short answers as stubs when thinking clearly has a much better quote
    better = _extract_english_answer_from_thinking(thinking) or _extract_persian_answer(
        "", thinking
    )
    if better and len(a) < 40 and len(better.strip()) > len(a) + 15:
        return True
    return False


async def _ollama_direct_answer(
    model: str,
    messages: list[dict],
    prefer_persian: bool,
    *,
    use_think: bool = True,
) -> str:
    """Non-streaming retry without thinking — used when Qwen only produced CoT."""
    retry_messages = [dict(m) for m in messages]
    if prefer_persian:
        for i in range(len(retry_messages) - 1, -1, -1):
            if retry_messages[i].get("role") == "user":
                user_content = retry_messages[i].get("content", "")
                extra = _qwen_user_turn_suffix(user_content, prefer_persian=True)
                if _is_continuation_request(user_content):
                    last_story = ""
                    for m in reversed(retry_messages):
                        if m.get("role") == "assistant":
                            last_story = (m.get("content") or "").strip()
                            break
                    if last_story:
                        extra = (
                            f"\n\n[ادامه این داستان را در ۳ خط کامل بنویس:\n"
                            f"{last_story}\n\n"
                            "بدون سلام. بدون استدلال انگلیسی.]"
                        )
                retry_messages[i] = {
                    **retry_messages[i],
                    "content": user_content + extra,
                }
                break
    else:
        for i in range(len(retry_messages) - 1, -1, -1):
            if retry_messages[i].get("role") == "user":
                retry_messages[i] = {
                    **retry_messages[i],
                    "content": (
                        retry_messages[i]["content"]
                        + _qwen_user_turn_suffix(
                            retry_messages[i]["content"], prefer_persian=False
                        )
                    ),
                }
                break

    req = {
        "model": model,
        "messages": retry_messages,
        "stream": False,
        "think": use_think if _is_qwen_model(model) else False,
        "options": _ollama_options(
            temperature=0.4,
            top_p=0.9,
            top_k=20,
            num_predict=min(1024, QWEN_NUM_PREDICT) if _is_qwen_model(model) else 2048,
        ),
        "keep_alive": OLLAMA_KEEP_ALIVE,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(f"{OLLAMA_URL}/api/chat", json=req)
        if response.status_code >= 400 and _is_cuda_runner_crash(response.text):
            await _unload_ollama_model(model)
            response = await client.post(f"{OLLAMA_URL}/api/chat", json=req)
        response.raise_for_status()
        data = response.json()
        msg = data.get("message") or {}
        content = (msg.get("content") or "").strip()
        thinking = (msg.get("thinking") or "").strip()
        if content and not _looks_like_chain_of_thought(content) and not _is_english_meta_dump(content):
            return content
        if _is_qwen_model(model):
            declared = _pull_declared_answer_from_thinking(
                thinking or content, prefer_persian=prefer_persian
            )
            if declared:
                return declared
            if thinking:
                extracted = _extract_persian_answer("", thinking, "") if prefer_persian else ""
                if not extracted:
                    extracted = _extract_english_answer_from_thinking(thinking)
                if extracted:
                    return extracted
        return content


def _needs_answer_retry(
    finalized: str,
    prefer_persian: bool,
    thinking: str = "",
) -> bool:
    if not (finalized or "").strip():
        return True
    if _is_generic_fallback(finalized):
        return True
    if _answer_looks_like_stub(finalized, thinking):
        return True
    if _is_qwen_instruction_leak(finalized) or _looks_like_chain_of_thought(finalized):
        return True
    if prefer_persian and (
        _is_english_meta_dump(finalized)
        or _looks_like_chain_of_thought(finalized)
        or not _is_mostly_persian(finalized)
    ):
        return True
    return False


def _extract_final_answer(
    text: str,
    identity: str,
    prefer_persian: bool,
    user_message: str = "",
    history_texts: Optional[list[str]] = None,
) -> str:
    """Turn a CoT / meta dump into a natural user-facing answer."""
    raw = (text or "").strip()
    history_texts = history_texts or []

    cleaned = _IDENTITY_PREFIX_RE.sub("", raw, count=1).lstrip() if raw else ""
    cleaned = _unwrap_meta_answer(cleaned)

    parts = _COT_MARKERS_RE.split(cleaned)
    if len(parts) > 1:
        cleaned = _unwrap_meta_answer(parts[-1].strip())

    # Natural Persian / English reply — reject punctuation stubs
    if cleaned and not _looks_like_chain_of_thought(cleaned) and not _is_trivial_answer(cleaned):
        if prefer_persian:
            persian_chunks = _persian_lines(cleaned)
            if persian_chunks:
                return "\n".join(persian_chunks[-4:]).strip()
            if len(_PERSIAN_ARABIC_RE.findall(cleaned)) > len(_LATIN_RE.findall(cleaned)):
                return cleaned.strip()
        else:
            return cleaned.strip()

    if prefer_persian and cleaned and not _is_trivial_answer(cleaned):
        # Meta English with a Persian quote already unwrapped above; try lines again
        persian_chunks = _persian_lines(_unwrap_meta_answer(cleaned))
        if persian_chunks:
            return "\n".join(persian_chunks[-4:]).strip()

    if (
        not cleaned
        or _is_trivial_answer(cleaned)
        or _looks_like_chain_of_thought(cleaned)
        or _is_english_meta_dump(cleaned)
        or (prefer_persian and not _is_mostly_persian(cleaned))
    ):
        # Don't substitute greetings/retell for creative tasks — let thinking extract / retry handle it
        if not _is_story_request(user_message):
            inferred = _infer_session_answer(
                user_message, history_texts, identity, prefer_persian
            )
            if inferred:
                return inferred
        if prefer_persian:
            return "متوجه سوال‌تان شدم، ولی پاسخ واضحی ساخته نشد. لطفاً دوباره بپرسید."
        return "I couldn't form a clear answer. Please ask again."

    return cleaned.strip()


def _sanitize_assistant_content(content: str) -> str:
    """Clean assistant text for context: strip thinking tags / meta — final answer only."""
    _, answer = _parse_model_output(content or "")
    cleaned = _IDENTITY_PREFIX_RE.sub("", answer, count=1).lstrip()
    if not cleaned or _is_generic_fallback(cleaned) or _is_trivial_answer(cleaned):
        return ""
    if _looks_like_chain_of_thought(cleaned) or _is_english_meta_dump(cleaned):
        persian_chunks = _persian_lines(cleaned)
        return "\n".join(persian_chunks[-3:]).strip() if persian_chunks else ""
    if _is_qwen_cot_fragment(cleaned):
        return ""
    return cleaned


def _flush_prefix_buffer(buffer: str) -> str:
    """Drop a leading identity intro once enough of the reply has arrived."""
    return _sanitize_assistant_content(buffer)


def _should_flush_prefix_buffer(buffer: str) -> bool:
    """Flush once we can safely strip an intro, or know there isn't one."""
    if not buffer:
        return False
    if len(buffer) >= _PREFIX_BUFFER_MAX or "\n" in buffer:
        return True

    # Clear non-intro start (e.g. Persian text) — don't delay normal replies
    if not re.match(r"^\s*I\s+am\b", buffer, flags=re.IGNORECASE):
        # Wait for a couple of characters so a partial "I" doesn't escape
        return len(buffer.strip()) >= 2

    # Identity-style start: wait until the first sentence ends and body begins
    return bool(
        _IDENTITY_PREFIX_RE.match(buffer)
        and re.search(r"[.!?]\s+\S", buffer)
    )


def _upsert_assistant_draft(session_id: int, db: Session, content: str) -> None:
    """Save partial assistant reply so refresh / session switch can reload it."""
    text = (content or "").strip()
    if not text:
        return
    last = _get_last_message(session_id, db)
    if last and last.sender == "assistant":
        last.message = text
    else:
        db.add(
            ChatMessage(
                session_id=session_id,
                sender="assistant",
                message=text,
            )
        )
    db.commit()


async def _upsert_assistant_draft_async(
    session_id: int,
    db: Session,
    content: str,
) -> None:
    await asyncio.to_thread(_upsert_assistant_draft, session_id, db, content)


def _is_explicitly_cancelled(
    session_id: int,
    generation_id: str,
    cancel_event: asyncio.Event,
) -> bool:
    return (
        cancel_event.is_set()
        or _stream_generation_ids.get(session_id) != generation_id
    )


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
        "is_generating": session_id in _stream_generation_ids,
        "messages": messages,
    }


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

    # Save user message (run sync DB off the event loop)
    user_msg = ChatMessage(
        session_id=session_id,
        sender="user",
        message=msg.message,
    )

    def _persist_user_turn() -> None:
        db.add(user_msg)
        db.commit()
        db.execute(
            ChatSession.__table__.update()
            .where(ChatSession.id == session_id)
            .values(updated_at=func.now())
        )
        db.commit()

    await asyncio.to_thread(_persist_user_turn)

    # Get selected model or use default (resolve qwen → cpu variant when available)
    selected_model = (msg.model or "").strip() or OLLAMA_MODEL
    display_model = selected_model
    selected_model = await _resolve_ollama_model(selected_model)
    print(f"[chat] session={session_id} using model={selected_model!r} (requested={msg.model!r})")

    # Get conversation history (system prompt uses the UI-selected model identity)
    history_limit = QWEN_HISTORY_MAX if _is_qwen_model(display_model) else 40
    conversation_history = await asyncio.to_thread(
        get_conversation_history,
        session_id,
        db,
        history_limit,
        display_model,
    )

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
    # Kill any leftover Ollama runner from a previous Stop before starting a new turn.
    await _abort_active_ollama_stream(session_id)

    cancel_event = asyncio.Event()
    _stream_cancel_events[session_id] = cancel_event
    generation_id = str(uuid.uuid4())
    _stream_generation_ids[session_id] = generation_id

    async def _generation_events(worker_db: Session) -> AsyncGenerator[str, None]:
        full_response = ""
        full_thinking = ""
        cancelled = False
        client_gone = False
        draft_save_counter = 0

        def is_explicitly_cancelled() -> bool:
            return _is_explicitly_cancelled(session_id, generation_id, cancel_event)

        try:
            yield f"data: [MODEL]{display_model}\n\n"

            is_qwen = _is_qwen_model(display_model)
            prefer_persian = _detect_reply_language(msg.message) == "Persian"
            think_flag = True if is_qwen else False
            ollama_options = (
                _qwen_stream_options()
                if is_qwen
                else _ollama_options(temperature=0.7, num_predict=2048)
            )
            content_accumulator = ""
            answer_started = False

            if is_explicitly_cancelled():
                cancelled = True
                yield "data: [CANCELLED]\n\n"
                return

            if await request.is_disconnected():
                client_gone = True

            ollama_request = {
                "model": selected_model,
                "messages": conversation_history,
                "stream": True,
                "think": think_flag,
                "keep_alive": OLLAMA_KEEP_ALIVE,
                "options": ollama_options,
            }

            async with httpx.AsyncClient(timeout=300.0) as client:
                _register_ollama_stream(
                    session_id,
                    client=client,
                    model=selected_model,
                )
                # One CUDA retry: unload crashed GPU runner, then reload with num_gpu=0.
                stream_response = None
                stream_ctx = None
                for _cuda_attempt in range(2):
                    if is_explicitly_cancelled():
                        cancelled = True
                        yield "data: [CANCELLED]\n\n"
                        return

                    stream_ctx = client.stream(
                        "POST",
                        f"{OLLAMA_URL}/api/chat",
                        json=ollama_request,
                    )
                    stream_response = await stream_ctx.__aenter__()
                    _set_ollama_stream_response(session_id, stream_response)
                    if is_explicitly_cancelled():
                        cancelled = True
                        try:
                            await stream_ctx.__aexit__(None, None, None)
                        except Exception:
                            pass
                        yield "data: [CANCELLED]\n\n"
                        return

                    if stream_response.status_code < 400:
                        break

                    error_body = (await stream_response.aread()).decode(
                        "utf-8", errors="replace"
                    )
                    try:
                        await stream_ctx.__aexit__(None, None, None)
                    except Exception:
                        pass
                    stream_ctx = None
                    stream_response = None
                    _set_ollama_stream_response(session_id, None)
                    try:
                        error_detail = json.loads(error_body).get("error", error_body)
                    except json.JSONDecodeError:
                        error_detail = error_body or "Ollama error"

                    if _cuda_attempt == 0 and _is_cuda_runner_crash(str(error_detail)):
                        await _unload_ollama_model(selected_model)
                        ollama_request["options"] = (
                            _qwen_stream_options()
                            if is_qwen
                            else _ollama_options(temperature=0.7, num_predict=2048)
                        )
                        continue

                    yield f"data: [ERROR] {error_detail}\n\n"
                    return

                if stream_response is None or stream_ctx is None:
                    yield "data: [ERROR] Ollama runner unavailable\n\n"
                    return

                response = stream_response
                try:
                    line_iter = response.aiter_lines().__aiter__()
                    # Never asyncio.wait_for()-cancel the httpx read: on slow CPU that
                    # drops tokens mid-stream (Qwen think collapses to a few chars).
                    # Stop still works: /cancel acloses the socket and the read errors out.
                    read_task: Optional[asyncio.Task] = asyncio.create_task(
                        line_iter.__anext__()
                    )
                    try:
                        while True:
                            if is_explicitly_cancelled():
                                cancelled = True
                                break

                            if await request.is_disconnected():
                                client_gone = True

                            assert read_task is not None
                            done, _ = await asyncio.wait({read_task}, timeout=0.25)
                            if not done:
                                continue

                            try:
                                line = read_task.result()
                            except StopAsyncIteration:
                                read_task = None
                                break
                            except (
                                httpx.ReadError,
                                httpx.StreamClosed,
                                httpx.RemoteProtocolError,
                                httpx.TransportError,
                            ):
                                # /cancel hung up the Ollama socket — stop reading.
                                read_task = None
                                cancelled = True
                                break
                            except Exception:
                                read_task = None
                                if is_explicitly_cancelled():
                                    cancelled = True
                                    break
                                raise

                            read_task = asyncio.create_task(line_iter.__anext__())

                            if not line.strip():
                                continue

                            try:
                                chunk_data = json.loads(line)
                            except json.JSONDecodeError:
                                continue

                            message_data = chunk_data.get("message", {})
                            content_chunk = message_data.get("content") or ""
                            thinking_chunk = message_data.get("thinking") or ""

                            if thinking_chunk:
                                full_thinking += thinking_chunk
                                if not client_gone:
                                    try:
                                        yield f"data: [THINK]{_encode_sse_chunk(thinking_chunk)}\n\n"
                                    except asyncio.CancelledError:
                                        client_gone = True

                            if content_chunk:
                                if is_qwen:
                                    content_accumulator += content_chunk
                                    route = _qwen_route_chunk(
                                        content_chunk,
                                        content_accumulator,
                                        prefer_persian,
                                        answer_started,
                                    )
                                    if route == "think":
                                        full_thinking += content_chunk
                                        if not client_gone:
                                            try:
                                                yield f"data: [THINK]{_encode_sse_chunk(content_chunk)}\n\n"
                                            except asyncio.CancelledError:
                                                client_gone = True
                                    else:
                                        answer_started = True
                                        full_response += content_chunk
                                        if not client_gone:
                                            try:
                                                yield f"data: {_encode_sse_chunk(content_chunk)}\n\n"
                                            except asyncio.CancelledError:
                                                client_gone = True
                                        draft_save_counter += 1
                                        if draft_save_counter == 1 or draft_save_counter % 8 == 0:
                                            draft = full_response.strip()
                                            if draft:
                                                try:
                                                    await _upsert_assistant_draft_async(
                                                        session_id, worker_db, draft
                                                    )
                                                except Exception:
                                                    pass
                                else:
                                    full_response += content_chunk
                                    if not client_gone:
                                        try:
                                            yield f"data: {_encode_sse_chunk(content_chunk)}\n\n"
                                        except asyncio.CancelledError:
                                            client_gone = True

                                    draft_save_counter += 1
                                    if draft_save_counter == 1 or draft_save_counter % 8 == 0:
                                        draft = full_response.strip()
                                        if draft:
                                            try:
                                                await _upsert_assistant_draft_async(
                                                    session_id, worker_db, draft
                                                )
                                            except Exception:
                                                pass

                            if chunk_data.get("done", False):
                                break
                    finally:
                        if read_task is not None and not read_task.done():
                            read_task.cancel()
                            try:
                                await read_task
                            except (asyncio.CancelledError, StopAsyncIteration, Exception):
                                pass

                    if cancelled:
                        try:
                            await response.aclose()
                        except Exception:
                            pass
                finally:
                    if stream_ctx is not None:
                        try:
                            await stream_ctx.__aexit__(None, None, None)
                        except Exception:
                            pass

            if is_explicitly_cancelled():
                cancelled = True
                # Persist whatever was streamed so far; do not delete the partial reply.
                partial = (full_response or "").strip()
                if partial:
                    try:
                        await _upsert_assistant_draft_async(
                            session_id, worker_db, partial
                        )
                    except Exception:
                        pass
                if not client_gone:
                    try:
                        yield "data: [CANCELLED]\n\n"
                    except asyncio.CancelledError:
                        client_gone = True
                return

            if full_thinking and not client_gone:
                try:
                    yield "data: [THINK_END]\n\n"
                except asyncio.CancelledError:
                    client_gone = True

            streamed_response = full_response.strip()
            full_response = streamed_response

            if is_qwen and not cancelled and not is_explicitly_cancelled():
                identity = _model_identity(display_model)
                history_all_texts = [
                    m.get("content", "")
                    for m in conversation_history
                    if m.get("role") in ("user", "assistant")
                ]
                history_user_texts = [
                    m.get("content", "")
                    for m in conversation_history
                    if m.get("role") == "user"
                ]

                finalized = _finalize_qwen_answer(
                    streamed_response,
                    full_thinking,
                    content_accumulator,
                    identity=identity,
                    prefer_persian=prefer_persian,
                    user_message=msg.message,
                    history_all_texts=history_all_texts,
                    history_user_texts=history_user_texts,
                )
                print(
                    f"[chat] qwen finalize session={session_id} "
                    f"streamed_len={len(streamed_response)} think_len={len(full_thinking)} "
                    f"final_len={len(finalized)} preview={finalized[:80]!r}"
                )

                if _needs_answer_retry(finalized, prefer_persian, full_thinking):
                    # One fast non-think retry only (think=True retry was too slow on CPU).
                    if not is_explicitly_cancelled():
                        try:
                            retry_answer = await asyncio.wait_for(
                                _ollama_direct_answer(
                                    selected_model,
                                    conversation_history,
                                    prefer_persian,
                                    use_think=False,
                                ),
                                timeout=45.0,
                            )
                            if (
                                not is_explicitly_cancelled()
                                and retry_answer
                                and not _needs_answer_retry(
                                    retry_answer, prefer_persian, ""
                                )
                            ):
                                finalized = retry_answer.strip()
                        except Exception as exc:
                            print(
                                f"[chat] qwen direct answer retry "
                                f"(think=False) failed: {type(exc).__name__}: {exc}"
                            )

                if (
                    not cancelled
                    and not is_explicitly_cancelled()
                    and not finalized
                    and not streamed_response
                ):
                    try:
                        async with httpx.AsyncClient(timeout=180.0) as fb_client:
                            _, fallback_answer = await _fetch_qwen_final_answer(
                                fb_client,
                                selected_model,
                                conversation_history,
                            )
                            if fallback_answer and not is_explicitly_cancelled():
                                finalized = fallback_answer.strip()
                    except Exception as exc:
                        print(f"[chat] qwen answer fallback failed: {exc}")

                if cancelled or is_explicitly_cancelled():
                    cancelled = True
                    partial = (streamed_response or "").strip()
                    if partial:
                        try:
                            await _upsert_assistant_draft_async(
                                session_id, worker_db, partial
                            )
                        except Exception:
                            pass
                    if not client_gone:
                        try:
                            yield "data: [CANCELLED]\n\n"
                        except asyncio.CancelledError:
                            client_gone = True
                    return

                if finalized:
                    full_response = finalized
                    if finalized != streamed_response and not client_gone:
                        try:
                            yield f"data: [FINAL]{_encode_sse_chunk(finalized)}\n\n"
                        except asyncio.CancelledError:
                            client_gone = True
                elif streamed_response:
                    full_response = streamed_response

            if is_explicitly_cancelled():
                cancelled = True
                partial = (full_response or "").strip()
                if partial:
                    try:
                        await _upsert_assistant_draft_async(
                            session_id, worker_db, partial
                        )
                    except Exception:
                        pass
                if not client_gone:
                    try:
                        yield "data: [CANCELLED]\n\n"
                    except asyncio.CancelledError:
                        client_gone = True
                return

            if full_response:
                try:
                    await _upsert_assistant_draft_async(
                        session_id, worker_db, full_response
                    )
                except Exception:
                    pass

                message_count = await asyncio.to_thread(
                    lambda: worker_db.query(ChatMessage)
                    .filter(ChatMessage.session_id == session_id)
                    .count()
                )

                if message_count == 2 and (not session.title or session.title == "New Chat"):
                    user_first_message = msg.message
                    short_title = user_first_message.strip()[:40].strip()
                    if len(user_first_message) > 40:
                        short_title += "..."
                    worker_db.execute(
                        ChatSession.__table__.update()
                        .where(ChatSession.id == session_id)
                        .values(title=short_title)
                    )
                    await asyncio.to_thread(worker_db.commit)

            if not client_gone:
                try:
                    yield "data: [DONE]\n\n"
                except asyncio.CancelledError:
                    client_gone = True

        except Exception as e:
            if not cancelled:
                try:
                    yield f"data: [ERROR] {str(e)}\n\n"
                except asyncio.CancelledError:
                    client_gone = True
        finally:
            # Drop registry entry; /cancel may already have closed the sockets.
            _active_ollama_streams.pop(session_id, None)
            # On cancel: keep the partial assistant draft (do not delete it).
            if _stream_generation_ids.get(session_id) == generation_id:
                _stream_generation_ids.pop(session_id, None)
            if _stream_cancel_events.get(session_id) is cancel_event:
                _stream_cancel_events.pop(session_id, None)

    event_queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def _run_generation_worker() -> None:
        worker_db = SessionLocal()
        try:
            async for event in _generation_events(worker_db):
                await event_queue.put(event)
        except Exception as exc:
            print(f"[chat] generation worker error: {exc}")
            await event_queue.put(f"data: [ERROR] {str(exc)}\n\n")
        finally:
            await event_queue.put(None)
            worker_db.close()

    asyncio.create_task(_run_generation_worker())

    async def stream_to_client() -> AsyncGenerator[str, None]:
        try:
            while True:
                item = await event_queue.get()
                if item is None:
                    break
                yield item
        except asyncio.CancelledError:
            # Client refreshed or navigated away — worker keeps generating in background
            pass

    return StreamingResponse(
        stream_to_client(),
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
    """Stop generation immediately. Keep user message and any partial assistant reply."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(404, "Conversation not found")

    if session_id in _stream_cancel_events:
        _stream_cancel_events[session_id].set()

    # Invalidate current generation so in-flight finalize/retry will not overwrite the partial.
    _stream_generation_ids.pop(session_id, None)
    # Hang up Ollama immediately so CPU inference stops (same as Ctrl+C / ollama stop).
    await _abort_active_ollama_stream(session_id)

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
