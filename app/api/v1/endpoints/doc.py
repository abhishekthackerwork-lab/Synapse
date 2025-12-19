from fastapi import APIRouter

from app.routes.document import router as document_routes

router = APIRouter()
router.include_router(document_routes)
