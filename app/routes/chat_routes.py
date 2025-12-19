from email.charset import CHARSETS

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.models.user import User
from app.db.session import get_async_session
from app.security.get_current_user import get_current_user
from app.services.chat_service import chat_service

from app.schemas.responses import SuccessResponse
from app.schemas.chat import ChatResponsePayload

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post(
    "/chat",
    response_model=SuccessResponse[ChatResponsePayload],
)
async def chat(
    message: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    result = await chat_service(
        message=message,
        files=files,
        user_id=current_user.id,
        session=session,
    )

    return SuccessResponse(data=result)