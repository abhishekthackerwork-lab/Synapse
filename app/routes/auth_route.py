from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.responses import SuccessResponse
from app.security.get_current_user import get_current_user
from app.db.session import get_async_session
from app.schemas.user import UserCreate, UserRead
from datetime import datetime, timedelta, timezone
from app.services.auth import get_user_by_email, create_user, authenticate_user
from app.security.vault_client import vault_client
from app.security.auth_config import (
    COOKIE_NAME,
    COOKIE_SECURE,
    COOKIE_SAMESITE,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ----------------------------------------------------------------------
# REGISTER (No login cookie here — secure default)
# ----------------------------------------------------------------------
@router.post(
    "/register",
    response_model=SuccessResponse[UserRead],
    status_code=201,
)
async def register_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_async_session),
):
    existing = await get_user_by_email(session, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await create_user(session, payload.email, payload.password)
    await session.commit()
    await session.refresh(user)

    return SuccessResponse(
        message="User registered successfully",
        data=user,
    )


# ----------------------------------------------------------------------
# LOGIN (Sets HttpOnly JWT cookie)
# ----------------------------------------------------------------------
@router.post(
    "/login",
    response_model=SuccessResponse[UserRead],
)
async def login_user(
    payload: UserCreate,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
):
    user = await authenticate_user(session, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    jwt_payload = {
        "sub": str(user.id),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    token = await vault_client.sign_jwt(jwt_payload)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return SuccessResponse(
        message="Login successful",
        data=user,
    )

# ----------------------------------------------------------------------
# /me endpoint
# ----------------------------------------------------------------------
@router.get("/me", response_model=UserRead)
async def me(current_user=Depends(get_current_user)):
    return current_user

# In app/routes/auth_route.py

@router.post("/logout")
async def logout_user(response: Response):
    """
    Removes the authentication cookie, effectively logging out the user.
    """
    # Instructs the browser to delete the cookie by setting max_age to 0
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )
    return {"message": "Successfully logged out"}