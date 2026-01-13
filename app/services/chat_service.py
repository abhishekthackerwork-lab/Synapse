from typing import List, Optional
from uuid import UUID, uuid4
import time

from qdrant_client.http import models as rest_models
from fastapi import HTTPException
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import exists

from app.db.models.chat import ChatMessage, ChatStatus
from app.schemas.chat import ChatInputPayload
from app.services.doc_upload import get_embedder, get_qdrant_client, retrieve
from app.services.ingestion_service import ingest_document
from app.services.qdrant_mapping import get_or_create_qdrant_user_id
from app.llm.GeminiManager import GeminiManager

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

async def chat_service(
    payload: ChatInputPayload,
    files: Optional[List[UploadFile]],
    user_id: UUID,
    session: AsyncSession,
):
    start_time = time.perf_counter()

    if files:
        validate_file(files)

    llm_result: dict | None = None
    llm_answer: str | None = None
    error_message: str | None = None
    model_name: str | None = None
    status = ChatStatus.PENDING

    message = payload.message
    if payload.conversation_id:
        stmt = select(
            exists().where(
                ChatMessage.conversation_id == payload.conversation_id,
                ChatMessage.user_id == user_id
            )
        )
        result = await session.execute(stmt)
        existing_owner = result.scalar_one_or_none()

        # Security Risk: If the ID exists but belongs to another user
        if existing_owner and existing_owner != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized access to chat history.")

        # 2. Assign or Generate the ID
    conv_id = payload.conversation_id or uuid4()

    try:
        # --------------------------------------------------
        # 1️⃣ Optional ingestion
        # --------------------------------------------------
        if files:
            for file in files:
                contents = await file.read()
                await ingest_document(
                    contents,
                    file.filename,
                    user_id,
                    session,
                )

        # --------------------------------------------------
        # 2️⃣ Retrieval
        # --------------------------------------------------
        embedder = get_embedder()
        qc = get_qdrant_client()

        qdrant_user_id = await get_or_create_qdrant_user_id(session, user_id)

        user_filter = rest_models.Filter(
            must=[
                rest_models.FieldCondition(
                    key="user_id",
                    match=rest_models.MatchValue(value=str(qdrant_user_id)),
                )
            ]
        )

        _, context = retrieve(
            query=message,
            embedder=embedder,
            qc=qc,
            collection="documents",
            top_k=5,
            filters=user_filter,
        )

        # --------------------------------------------------
        # 3️⃣ LLM call
        # --------------------------------------------------
        gm = GeminiManager()
        model_name = gm.model_name

        print("DEBUG: Starting LLM call...")


        llm_result = await gm.generate_response(
            query=message,
            conversation_id=conv_id,
            context=context,
            session=session,
            user_id = user_id,
        )

        print("DEBUG: LLM call finished!")

        status = ChatStatus.COMPLETED

        # Extract the string from the result dictionary
        actual_answer = llm_result.get("answer") if llm_result else "No response generated"

        return_payload = {
            "answer": actual_answer,
            "conversation_id": conv_id,
        }


    except Exception as exc:
        error_message = str(exc)
        status = ChatStatus.ERROR      # ❌ failure
        raise

    finally:
        # --------------------------------------------------
        # 4️⃣ Persist chat message (atomic DB write)
        # --------------------------------------------------
        try:
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # We safely extract values using .get() in case llm_result is None (on error)
            chat_row = ChatMessage(
                user_id=user_id,
                conversation_id=conv_id,
                user_message=message,
                llm_response=llm_result.get("answer") if llm_result else None,
                thought_signature=llm_result.get("thought_signature") if llm_result else None,
                tool_trace=llm_result.get("tool_trace") if llm_result else None,
                model_name=model_name,
                latency_ms=latency_ms,
                error_message=error_message,
                status=status,
            )

            session.add(chat_row)
            await session.commit()

        except Exception as db_exc:
            print(f"DEBUG: Database failed but moving on: {db_exc}")
            await session.rollback()

    return return_payload

def validate_file(files: Optional[List[UploadFile]]):
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension: {ext}",
            )

        file.file.seek(0, 2) # move to the end of the file
        size = file.file.tell()
        file.file.seek(0)

        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large, Max file upload of 50 MB",
            )
