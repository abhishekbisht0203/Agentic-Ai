"""Workflow management and execution router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token
from app.models.user import User
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowDetail,
    WorkflowExecutionList,
    WorkflowExecutionResponse,
    WorkflowExecuteRequest,
    WorkflowList,
    WorkflowResponse,
    WorkflowUpdate,
)
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["Workflows"])

CurrentUser = Annotated[User, Depends(get_current_user_from_token)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def _get_workflow_service(db: DbSession) -> WorkflowService:
    return WorkflowService(db)


@router.post(
    "/",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workflow",
)
async def create_workflow(
    data: WorkflowCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> WorkflowResponse:
    service = _get_workflow_service(db)
    return await service.create_workflow(user_id=current_user.id, data=data)


@router.get(
    "/",
    response_model=WorkflowList,
    summary="List workflows for the current user",
)
async def list_workflows(
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> WorkflowList:
    service = _get_workflow_service(db)
    return await service.list_workflows(
        user_id=current_user.id, page=page, page_size=page_size
    )


@router.get(
    "/{workflow_id}",
    response_model=WorkflowDetail,
    summary="Get workflow details",
)
async def get_workflow(
    workflow_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> WorkflowDetail:
    service = _get_workflow_service(db)
    return await service.get_workflow(workflow_id=workflow_id, user_id=current_user.id)


@router.put(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Update a workflow",
)
async def update_workflow(
    workflow_id: uuid.UUID,
    data: WorkflowUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> WorkflowResponse:
    service = _get_workflow_service(db)
    return await service.update_workflow(
        workflow_id=workflow_id, user_id=current_user.id, data=data
    )


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workflow",
)
async def delete_workflow(
    workflow_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    service = _get_workflow_service(db)
    await service.delete_workflow(workflow_id=workflow_id, user_id=current_user.id)


@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute a workflow",
)
async def execute_workflow(
    workflow_id: uuid.UUID,
    data: WorkflowExecuteRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> WorkflowExecutionResponse:
    service = _get_workflow_service(db)
    return await service.execute_workflow(
        workflow_id=workflow_id, user_id=current_user.id, data=data
    )


@router.get(
    "/{workflow_id}/executions",
    response_model=WorkflowExecutionList,
    summary="List executions for a workflow",
)
async def list_executions(
    workflow_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> WorkflowExecutionList:
    service = _get_workflow_service(db)
    return await service.list_executions(
        workflow_id=workflow_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/executions/{execution_id}",
    response_model=WorkflowExecutionResponse,
    summary="Get execution details",
)
async def get_execution(
    execution_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> WorkflowExecutionResponse:
    service = _get_workflow_service(db)
    return await service.get_execution(
        execution_id=execution_id, user_id=current_user.id
    )


@router.post(
    "/executions/{execution_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a running execution",
)
async def cancel_execution(
    execution_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    service = _get_workflow_service(db)
    await service.cancel_execution(
        execution_id=execution_id, user_id=current_user.id
    )
