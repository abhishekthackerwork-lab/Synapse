from typing import List, Optional
from uuid import UUID

from qdrant_client.http import models as rest_models

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.doc_upload import get_embedder, get_qdrant_client, retrieve
from app.services.ingestion_service import ingest_document
from app.services.qdrant_mapping import get_or_create_qdrant_user_id
from app.llm.GeminiManager import GeminiManager

async def chat_service(
    message: str,
    files: Optional[List[UploadFile]],
    user_id: UUID,
    session: AsyncSession,
):
    try:
        # 1️⃣ Optional ingestion
        if files:
            for file in files:
                contents = await file.read()
                await ingest_document(
                    contents,
                    file.filename,
                    user_id,
                    session,
                )

        # 2️⃣ Retrieval
        embedder = get_embedder()
        qc = get_qdrant_client()

        qdrant_user_id = await get_or_create_qdrant_user_id(session, user_id)

        user_filter = rest_models.Filter(
            must=[
                rest_models.FieldCondition(
                    key="user_id",  # qdrant_user_id stored under this key
                    match=rest_models.MatchValue(value=str(qdrant_user_id))
                )
            ]
        )

        hits, context = retrieve(
            query=message,
            embedder=embedder,
            qc=qc,
            collection="documents",
            top_k=5,
            filters=user_filter,
        )

        # 3️⃣ LLM call
        gm = GeminiManager()

        answer = await gm.generate_response(
            query=message,
            context=context,
        )

        return {
            "answer": answer,
        }
    except Exception:
        await session.rollback()
        raise
