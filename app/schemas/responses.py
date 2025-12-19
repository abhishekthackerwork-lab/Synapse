# app/schemas/response.py

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    data: T
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None