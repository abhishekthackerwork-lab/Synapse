from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from jose import jwt

from app.db.session import get_async_session
from app.schemas.user import UserRead
from app.services.auth import get_user
from app.security.public_key import PUBLIC_KEY
from app.security.auth_config import COOKIE_NAME  # moved from settings


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
) -> UserRead:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Verify with ES256 public key
        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["ES256"]
        )

        user_id = UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
