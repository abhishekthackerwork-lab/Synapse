# app/schemas/chat.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import Form

from pydantic import BaseModel, Field

from app.db.models.chat import ChatStatus


class ChatResponsePayload(BaseModel):
    answer: str
    conversation_id: UUID

class ChatInputPayload(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None

    # This classmethod allows us to use the model as a Form dependency
    @classmethod
    def as_form(
        cls,
        message: str = Form(...),
        conversation_id: Optional[UUID] = Form(None)
    ):
        return cls(message=message, conversation_id=conversation_id)

class ConversationSummary(BaseModel):
    conversation_id: UUID
    title: str
    created_at: datetime

class MessageHistoryResponse(BaseModel):
    message_id: UUID
    user_message: str
    llm_response: Optional[str]
    status: ChatStatus
    created_at: datetime

    class Config:
        from_attributes = True