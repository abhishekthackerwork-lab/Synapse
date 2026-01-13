from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Text,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base
from app.db.models.mixins import TimeStampMixin
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class Task(Base, TimeStampMixin):
    __tablename__ = "tasks"
    __table_args__ = {"schema": "app"}

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    conversation_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    created_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("app.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    status = Column(
        PG_ENUM(
            TaskStatus,
            name="task_status_final",
            schema="app",
            # This tells SQLAlchemy: "Use the .value (lowercase) not the .name (uppercase)"
            values_callable=lambda obj: [e.value for e in obj]
        ),
        nullable=False,
        default=TaskStatus.TODO
    )
