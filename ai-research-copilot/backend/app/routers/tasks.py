"""Background task management router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token
from app.models.user import User
from app.schemas.task import TaskList, TaskResponse
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])

CurrentUser = Annotated[User, Depends(get_current_user_from_token)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


class TaskCreateRequest(BaseModel):
    """Request body for creating a background task."""

    task_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Category of the task (e.g. 'document_processing').",
    )
    input_data: dict | None = Field(
        default=None,
        description="Optional payload describing the work to be done.",
    )
    priority: int = Field(
        default=0,
        description="Numeric priority (higher = more urgent).",
    )


def _get_task_service(db: DbSession) -> TaskService:
    return TaskService(db)


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new background task",
)
async def create_task(
    data: TaskCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskResponse:
    service = _get_task_service(db)
    return await service.create_task(
        user_id=current_user.id,
        task_type=data.task_type,
        input_data=data.input_data,
        priority=data.priority,
    )


@router.get(
    "/",
    response_model=TaskList,
    summary="List tasks for the current user",
)
async def list_tasks(
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TaskList:
    service = _get_task_service(db)
    return await service.list_tasks(
        user_id=current_user.id, page=page, page_size=page_size
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task details",
)
async def get_task(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskResponse:
    service = _get_task_service(db)
    return await service.get_task(task_id=task_id, user_id=current_user.id)


@router.post(
    "/{task_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a running task",
)
async def cancel_task(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    service = _get_task_service(db)
    await service.cancel_task(task_id=task_id, user_id=current_user.id)
