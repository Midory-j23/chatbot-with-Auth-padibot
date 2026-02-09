from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class MessageOut(BaseModel):
    id: int
    session_id: int
    sender: str  # "user" | "assistant"
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class SessionSummary(BaseModel):
    id: int
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_message_preview: Optional[str] = None  # optional, can be computed

    class Config:
        from_attributes = True


class SessionDetail(SessionSummary):
    messages: List[MessageOut] = []


class SessionCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)


class SessionUpdate(BaseModel):
    title: str = Field(..., max_length=200)


class MessageCreate(BaseModel):
    message: str
    image: Optional[str] = None  # base64, URL, or null