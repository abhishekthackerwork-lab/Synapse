import os
import uuid
import logging
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models

from app.db.models.qdrant import Document, Chunk, UserVectorIdentity
from app.services.qdrant_mapping import (
    get_or_create_qdrant_user_id,
    create_document,
    create_chunk,
)
from app.utils.logger import log_service, logger, log_exception, log_warning, log_service_error
from app.services.doc_upload import get_qdrant_client  # see note below
from app.services.doc_upload import get_embedder, Embedder  # lightweight wrapper around your Embedder class
from app.services.doc_upload import process_file_sync, save_temp_file_sync  # CPU helpers

DEFAULT_COLLECTION = "documents"
BATCH_SIZE = 32
CHUNK_SIZE = 800
OVERLAP = 100

def _make_payload(
    qdrant_user_id: str,
    doc_id: str,
    chunk_id: str,
    chunk_index: int,
    page: int | None,
    filename: str,
    source_type: str,
    embedding_model: str,
    text_preview: str,
) -> dict:
    """
    standardizes the payload stored in qdrant
    """

    return {
        "user_id": str(qdrant_user_id),
        "doc_id": str(doc_id),
        "chunk_id": str(chunk_id),
        "chunk_index": chunk_index,
        "page": page,
        "source": filename,
        "source_type": source_type,
        "embedding_model": embedding_model,
        "timestamp": datetime.utcnow().isoformat(),
        "text_preview": text_preview,
    }

def _prepare_qdrant_points(
    vectors_with_meta: List[dict]
) -> List[rest_models.PointStruct]:
    """
    Convert vector+meta dicts to rest_models.PointStruct list.
    Each element in vectors_with_meta should contain:
      - qdrant_point_id: UUID | str
      - vector: List[float]
      - payload: dict
    """

    points = []
    for item in vectors_with_meta:
        points.append(
            rest_models.PointStruct(
                id = str(item["qdrant_point_id"]),
                vector = item["vector"],
                payload = item["payload"],
            )
        )
    return points

def _upsert_to_qdrant_sync(
    qc: QdrantClient,
    collection: str,
    points: list[rest_models.PointStruct],
):
    for i in range(0, len(points), BATCH_SIZE):
        chunk = points[i : i + BATCH_SIZE]
        qc.upsert(
            collection_name=collection,
            points=chunk,   # ✅ correct
        )


@log_service
async def ingest_document(
    file_bytes: bytes,
    filename: str,
    user_id: uuid.UUID,
    session: AsyncSession,
    collection: str = DEFAULT_COLLECTION,
) -> Dict[str, Any]:
    temp_path = None
    qc = None

    try:
        # 1) save file sync in threadpool
        temp_path = await run_in_threadpool(save_temp_file_sync, file_bytes, filename)

        # 2) CPU-bound: extract/split/embed inside threadpool
        embedder: Embedder = await run_in_threadpool(get_embedder)
        cpu_result = await run_in_threadpool(process_file_sync, temp_path, embedder, CHUNK_SIZE, OVERLAP)

        if not cpu_result:
            return {"vectors": 0, "document_id": None}

        # 3a) qdrant user id
        qdrant_user_id = await get_or_create_qdrant_user_id(session, user_id)

        # 3b) create document row (deterministic doc_id)
        doc_id = uuid.uuid4()
        await create_document(
            session,
            user_id=user_id,
            filename=filename,
            file_size=len(file_bytes),
            metadata={"uploaded_via": "api"},
            doc_id=doc_id,
        )

        # 3c) prepare chunk DB rows and qdrant payloads (collect first)
        vectors_with_meta: List[dict] = []
        for idx, item in enumerate(cpu_result):
            chunk_id = uuid.uuid4()
            qdrant_point_id = uuid.uuid4()

            # add DB chunk (no commit)
            await create_chunk(
                session,
                doc_id=doc_id,
                chunk_index=idx,
                qdrant_point_id=qdrant_point_id,
                embedding_model=embedder.model_name,
                length_tokens=item.get("length_tokens"),
                chunk_id=chunk_id,
            )

            payload = _make_payload(
                qdrant_user_id=qdrant_user_id,
                doc_id=doc_id,
                chunk_id=chunk_id,
                chunk_index=idx,
                page=item.get("page"),
                filename=os.path.basename(filename),
                source_type=Path(filename).suffix.replace(".", ""),
                embedding_model=embedder.model_name,
                text_preview=item.get("text_preview", "")[:300],
            )

            vectors_with_meta.append(
                {
                    "qdrant_point_id": qdrant_point_id,
                    "vector": item.get("vector"),
                    "payload": payload,
                }
            )

        # 4) ensure collection exists (blocking, run in threadpool)
        qc = get_qdrant_client()
        # Use "ensure" semantics; do NOT recreate (which deletes existing data)
        try:
            await run_in_threadpool(qc.get_collection, collection)
        except Exception:
            # create if missing
            await run_in_threadpool(qc.recreate_collection, collection,
                                    rest_models.VectorParams(size=embedder.dim, distance=rest_models.Distance.COSINE))

        # 5) prepare PointStructs and upsert (blocking) in threadpool
        points = _prepare_qdrant_points(vectors_with_meta)
        await run_in_threadpool(_upsert_to_qdrant_sync, qc, collection, points)

        # 6) commit DB only after Qdrant succeeded
        return {"vectors": len(points), "document_id": str(doc_id)}

    except Exception as exc:
        logger.exception("ingest_document failed")
        raise

    finally:
        # cleanup temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                log_warning("Failed to remove temp file %s", temp_path)
