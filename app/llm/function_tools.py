from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4
from pydantic import BaseModel
from typing import Optional, Literal
from uuid import UUID

from sqlalchemy import select, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import task
from app.db.models.task import Task
from app.db.models.task import TaskStatus

class ToolExecutionError(Exception):
    """User-visible tool execution error."""
    pass



class ManageTaskArgs(BaseModel):
    action: Literal["create", "update", "delete", "list"]

    query: Optional[str] = None
    conversation_id: Optional[UUID] = None

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["todo", "in_progress", "done"]] = None
    deadline: Optional[datetime] = None

async def _resolve_single_task_by_query (
        *,
        query: str,
        user_id: UUID,
        session: AsyncSession,
) -> Optional[Task]:
    stmt = (
        select(Task)
        .where(
            Task.created_by_user_id == user_id,
            or_(
                Task.title.ilike(f"%{query}%"),
                Task.description.ilike(f"%{query}%"),
            ),
        )
        .order_by(Task.created_at.desc())
    )

    result = await session.execute(stmt)
    tasks = result.scalars().all()

    if not tasks:
        raise ToolExecutionError("No matching task found")

    if len(tasks) > 1:
        raise ToolExecutionError("Multiple matching tasks found")

    return tasks[0]

async def create_task (
        *,
        args: ManageTaskArgs,
        user_id: UUID,
        session: AsyncSession,
) -> Dict:
    if not args.conversation_id:
        raise ToolExecutionError("conversation id is required")
    if not args.title:
        raise ToolExecutionError("title is required")

    task = Task(
        task_id = uuid4(),
        conversation_id = args.conversation_id,
        title = args.title,
        description = args.description,
        status = args.status or "todo",
        created_by_user_id = user_id,
    )

    session.add(task)
    await session.flush()
    await session.refresh(task)

    return {
        "title": task.title,
        "status": task.status.value,
    }


async def update_task(
    *,
    args: ManageTaskArgs,
    user_id: UUID,
    session: AsyncSession,
) -> Dict:
    if not args.query:
        raise ToolExecutionError("query is required")

    # Resolver already enforces:
    # - ownership
    # - exactly one match
    task = await _resolve_single_task_by_query(
        query=args.query,
        user_id=user_id,
        session=session,
    )

    if not any([args.status, args.title, args.description,]):
        raise ToolExecutionError("No fields provided to update")

    updated_fields = []
    if args.status:
        task.status = TaskStatus(args.status)
        updated_fields.append("status")
    if args.title:
        task.title = args.title
        updated_fields.append("title")
    if args.description:
        task.description = args.description
        updated_fields.append("description")

    await session.flush()

    return {
        "updated": True,
        "updated_fields": updated_fields,
        "status": task.status.value,
    }

from sqlalchemy import delete


async def delete_task(
    *,
    args: ManageTaskArgs,
    user_id: UUID,
    session: AsyncSession,
) -> dict:
    if not args.query:
        raise ToolExecutionError("query is required to identify the task to delete")

    task = await _resolve_single_task_by_query(
        query=args.query,
        user_id=user_id,
        session=session,
    )

    await session.delete(task)

    return {
        "action": "delete",
        "deleted": True,
        "task": {
            "title": task.title,
            "status": task.status.value,
        },
    }

from sqlalchemy import select


async def list_tasks(
    *,
    args: ManageTaskArgs,
    user_id: UUID,
    session: AsyncSession,
) -> dict:
    # 1. Base query - Filter ONLY by user_id for a global list
    stmt = select(Task).where(
        Task.created_by_user_id == user_id,
    )

    # 2. Filter by Status (if Gemini provides it)
    if args.status:
        stmt = stmt.where(Task.status == args.status.lower())

    # 3. Filter by Keyword (if Gemini provides it)
    if args.query:
        # The % wildcards allow matching anywhere in the string
        search_pattern = f"%{args.query}%"
        stmt = stmt.where(
            or_(
                Task.title.ilike(search_pattern),
                Task.description.ilike(search_pattern),
            )
        )

    stmt = stmt.order_by(Task.created_at.desc())

    result = await session.execute(stmt)
    tasks = result.scalars().all()

    return {
        "action": "list",
        "filter_applied": {"status": args.status, "query": args.query},
        "count": len(tasks),
        "tasks": [
            {
                "title": task.title,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
            }
            for task in tasks
        ],
    }

async def manage_task(
    *,
    args: ManageTaskArgs,
    user_id: UUID,
    session: AsyncSession,
) -> dict:
    # DEBUG LOGGING
    print(
        f"[DEBUG] manage_task dispatcher called. Action='{args.action}' | Title='{args.title}' | Deadline='{args.deadline}'")

    try:
        if args.action == "create":
            return await create_task(args=args, user_id=user_id, session=session)

        if args.action == "update":
            return await update_task(args=args, user_id=user_id, session=session)

        if args.action == "delete":
            return await delete_task(args=args, user_id=user_id, session=session)

        if args.action == "list":
            return await list_tasks(args=args, user_id=user_id, session=session)

        raise ToolExecutionError(f"Unsupported action: {args.action}")
    except ToolExecutionError:
        await session.rollback()
        raise
