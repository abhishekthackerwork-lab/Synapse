from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.doc import router as docs_router
from app.api.v1.endpoints.chat import router as chat_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(docs_router)
api_router.include_router(chat_router)