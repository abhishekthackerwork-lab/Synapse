# app/schemas/chat.py

from pydantic import BaseModel

class ChatResponsePayload(BaseModel):
    answer: str
