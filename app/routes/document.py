from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from app.db.models.user import User
from app.db.session import get_async_session
from app.security.get_current_user import get_current_user
from app.services.doc_upload import get_embedder, get_qdrant_client, retrieve
from fastapi.concurrency import run_in_threadpool
from qdrant_client.http import models as rest_models
from app.db.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ingestion_service import ingest_document
from app.services.qdrant_mapping import get_or_create_qdrant_user_id

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    contents = await file.read()
    try:
        result = await ingest_document(contents, file.filename, current_user.id, session)
        return {"status": 200, "vectors": result["vectors"], "document_id": result["document_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search(
    q: str = None,
    top_k: int = 5,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    embedder = get_embedder()
    qc = get_qdrant_client()

    qdrant_user_id = await get_or_create_qdrant_user_id(
        session,
        current_user.id
    )

    user_filter = rest_models.Filter(
        must=[
            rest_models.FieldCondition(
                key="user_id",  # payload key
                match=rest_models.MatchValue(value=str(qdrant_user_id))
            )
        ]
    )

    hits, chunks = retrieve(
        q,
        embedder,
        qc,
        collection="documents",
        top_k=top_k,
        filters=user_filter   # <-- USER FILTER HERE
    )

    return {
        "hits": len(hits),
        "chunks": chunks
    }
