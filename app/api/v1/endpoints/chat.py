from fastapi import APIRouter

from app.routes.chat_routes import router as chat_routes

router = APIRouter()
router.include_router(chat_routes)
