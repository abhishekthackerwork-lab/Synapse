from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    JSON,
    Index,
    Text,
    Enum,
    LargeBinary,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base
from app.db.models.mixins import TimeStampMixin



class ChatStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"

class ChatMessage(Base, TimeStampMixin):
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("idx_chat_user_created", "user_id", "created_at"),
        {"schema": "app"},
    )

    message_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Ownership
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("app.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    conversation_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Core content
    user_message = Column(Text, nullable=False)
    llm_response = Column(Text, nullable=True)
    thought_signature = Column(LargeBinary, nullable=True)

    # LLM metadata
    model_name = Column(String, nullable=True)
    latency_ms = Column(Integer, nullable=True)

    tool_trace = Column(JSONB, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Execution status
    status = Column(
        Enum(
            ChatStatus,
            name="chat_status_enum",
            create_type=False,  # Alembic controls this
        ),
        nullable=False,
        default=ChatStatus.PENDING,
        index=True,
    )

    user = relationship("User", backref="chat_messages")