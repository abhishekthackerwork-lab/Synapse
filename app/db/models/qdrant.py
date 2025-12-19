from sqlalchemy import (
    Column, String, Integer, BigInteger, ForeignKey, JSON, TIMESTAMP, func, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base
from app.db.models.mixins import TimeStampMixin
from app.db.models.user import User


class UserVectorIdentity(Base, TimeStampMixin):
    __tablename__ = "user_vector_identity"
    __table_args__ = {"schema": "app"}

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("app.users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    qdrant_user_id = Column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid.uuid4,
        index=True,
    )

    user = relationship("User", backref="vector_identity", uselist=False)


class Document(Base, TimeStampMixin):
    __tablename__ = "documents"
    __table_args__ = {"schema": "app"}

    doc_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("app.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    filename = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    uploaded_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now()
    )

    extra_metadata = Column(JSON, nullable=False, default=dict)

    user = relationship("User", backref="documents")
    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )


class Chunk(Base, TimeStampMixin):
    __tablename__ = "chunks"
    __table_args__ = (
        Index("idx_chunk_doc_index", "doc_id", "chunk_index"),
        {"schema": "app"},
    )

    chunk_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    doc_id = Column(
        UUID(as_uuid=True),
        ForeignKey("app.documents.doc_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chunk_index = Column(Integer, nullable=False)

    qdrant_point_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        index=True,
    )

    embedding_model = Column(String, nullable=True)
    length_tokens = Column(Integer, nullable=True)

    document = relationship("Document", back_populates="chunks")
