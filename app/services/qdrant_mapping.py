from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.db.models.qdrant import UserVectorIdentity, Document, Chunk


# ------------------------------------------------------
# 1. Get or create Qdrant user identity
# ------------------------------------------------------
async def get_or_create_qdrant_user_id(
    session: AsyncSession,
    user_id: uuid.UUID
) -> uuid.UUID:

    stmt = select(UserVectorIdentity).where(UserVectorIdentity.user_id == user_id)
    result = await session.execute(stmt)
    identity = result.scalar_one_or_none()

    if identity:
        return identity.qdrant_user_id

    new_identity = UserVectorIdentity(
        user_id=user_id,
        qdrant_user_id=uuid.uuid4(),
    )

    session.add(new_identity)

    # ✅ REQUIRED: make row exist inside transaction
    await session.flush()

    return new_identity.qdrant_user_id

# ------------------------------------------------------
# 2. Create a Document row with server-generated doc_id
# ------------------------------------------------------
async def create_document(
    session: AsyncSession,
    user_id: uuid.UUID,
    filename: str,
    file_size: int,
    metadata: dict,
    doc_id: uuid.UUID,
) -> uuid.UUID:

    doc = Document(
        doc_id=doc_id,
        user_id=user_id,
        filename=filename,
        file_size=file_size,
        extra_metadata=metadata,
    )

    session.add(doc)
    return doc.doc_id


# ------------------------------------------------------
# 3. Create a Chunk row
# ------------------------------------------------------
async def create_chunk(
    session: AsyncSession,
    doc_id: uuid.UUID,
    chunk_index: int,
    qdrant_point_id: uuid.UUID,
    embedding_model: str,
    length_tokens: int,
    chunk_id: uuid.UUID,
) -> uuid.UUID:

    chunk = Chunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        chunk_index=chunk_index,
        qdrant_point_id=qdrant_point_id,
        embedding_model=embedding_model,
        length_tokens=length_tokens,
    )

    session.add(chunk)
    return chunk.chunk_id
