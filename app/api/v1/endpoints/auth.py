from fastapi import APIRouter

from app.routes.auth_route import router as auth_routes

router = APIRouter()
router.include_router(auth_routes)
