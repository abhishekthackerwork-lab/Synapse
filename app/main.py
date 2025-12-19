from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.db.session import init_db_engine
from app.api.api import api_router

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.services.doc_upload import get_qdrant_client, get_embedder, ensure_collection

app = FastAPI(title="Synapse Backend", version="0.1.0")

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

origins = [
    "http://localhost:5173",  # Your React development server
    "http://127.0.0.1:5173",
    # Add other domains here when deploying
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,              # ONLY allow requests from your frontend's address
    allow_credentials=True,             # Allows cookies/auth headers to be sent
    allow_methods=["*"],                # Allows GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],                # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    # 1️⃣ Initialize database (async)
    await init_db_engine()

    # 2️⃣ Initialize vector store schema (sync)
    qc = get_qdrant_client()
    embedder = get_embedder()

    ensure_collection(
        qc=qc,
        collection_name="documents",
        vector_size=embedder.dim,
    )


@app.get("/health")
async def health_check():
    """
    Health Check Endpoint to verify container connectivity.
    """
    return {
        "status": "healthy",
        "service": "Synapse API",
        "environment": "Development"
    }

app.include_router(api_router, prefix="/api/v1")