"""Agent configuration and execution router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token
from app.models.user import User
from app.schemas.agent import (
    AgentConfigurationCreate,
    AgentConfigurationDetail,
    AgentConfigurationList,
    AgentConfigurationResponse,
    AgentConfigurationUpdate,
    AgentExecuteRequest,
    AgentExecuteResponse,
)
from app.schemas.task import TaskResponse
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["Agents"])

CurrentUser = Annotated[User, Depends(get_current_user_from_token)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def _get_agent_service(db: DbSession) -> AgentService:
    return AgentService(db)


@router.post(
    "/configurations",
    response_model=AgentConfigurationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent configuration",
)
async def create_agent_configuration(
    data: AgentConfigurationCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> AgentConfigurationResponse:
    service = _get_agent_service(db)
    return await service.create_agent_config(data=data)


@router.get(
    "/configurations",
    response_model=AgentConfigurationList,
    summary="List agent configurations",
)
async def list_agent_configurations(
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 100,
) -> AgentConfigurationList:
    service = _get_agent_service(db)
    return await service.list_agent_configs(page=page, page_size=page_size)


@router.get(
    "/configurations/{config_id}",
    response_model=AgentConfigurationDetail,
    summary="Get agent configuration details",
)
async def get_agent_configuration(
    config_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> AgentConfigurationDetail:
    service = _get_agent_service(db)
    return await service.get_agent_config(config_id=config_id)


@router.put(
    "/configurations/{config_id}",
    response_model=AgentConfigurationResponse,
    summary="Update an agent configuration",
)
async def update_agent_configuration(
    config_id: uuid.UUID,
    data: AgentConfigurationUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> AgentConfigurationResponse:
    service = _get_agent_service(db)
    return await service.update_agent_config(config_id=config_id, data=data)


@router.delete(
    "/configurations/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an agent configuration",
)
async def delete_agent_configuration(
    config_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    service = _get_agent_service(db)
    await service.delete_agent_config(config_id=config_id)


@router.post(
    "/execute",
    response_model=AgentExecuteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute an agent task",
)
async def execute_agent(
    data: AgentExecuteRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> AgentExecuteResponse:
    service = _get_agent_service(db)
    return await service.execute_agent(user_id=current_user.id, data=data)


@router.get(
    "/status/{task_id}",
    response_model=TaskResponse,
    summary="Get agent execution status",
)
async def get_agent_status(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskResponse:
    service = _get_agent_service(db)
    return await service.get_agent_status(task_id=task_id)
