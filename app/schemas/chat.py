# app/schemas/chat.py
from typing import Optional
from uuid import UUID
from fastapi import Form

from pydantic import BaseModel, Field

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