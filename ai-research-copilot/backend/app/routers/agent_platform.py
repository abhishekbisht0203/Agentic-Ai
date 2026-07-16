"""Agent platform router - full CRUD, run, chat, memory, tools."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token
from app.models.user import User
from app.schemas.agent_platform import (
    AgentChatRequest,
    AgentCreate,
    AgentDuplicate,
    AgentList,
    AgentMemoryResponse,
    AgentResponse,
    AgentRunList,
    AgentToolResponse,
    AgentUpdate,
    AgentWithStats,
)
from app.services.agent_platform_service import AgentPlatformService

router = APIRouter(prefix="/agent-platform", tags=["Agent Platform"])

CurrentUser = Annotated[User, Depends(get_current_user_from_token)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def _get_service(db: DbSession) -> AgentPlatformService:
    return AgentPlatformService(db)


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(
    data: AgentCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> AgentResponse:
    service = _get_service(db)
    return await service.create_agent(user_id=current_user.id, data=data)


@router.get("/agents", response_model=AgentList)
async def list_agents(
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 100,
    search: str | None = Query(default=None, max_length=255),
) -> AgentList:
    service = _get_service(db)
    return await service.list_agents(user_id=current_user.id, page=page, page_size=page_size, search=search)


@router.get("/agents/{agent_id}", response_model=AgentWithStats)
async def get_agent(
    agent_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> AgentWithStats:
    service = _get_service(db)
    return await service.get_agent(agent_id=agent_id, user_id=current_user.id)


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    data: AgentUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> AgentResponse:
    service = _get_service(db)
    return await service.update_agent(agent_id=agent_id, user_id=current_user.id, data=data)


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    service = _get_service(db)
    await service.delete_agent(agent_id=agent_id, user_id=current_user.id)


@router.post("/agents/{agent_id}/duplicate", response_model=AgentResponse, status_code=201)
async def duplicate_agent(
    agent_id: uuid.UUID,
    data: AgentDuplicate,
    current_user: CurrentUser,
    db: DbSession,
) -> AgentResponse:
    service = _get_service(db)
    return await service.duplicate_agent(agent_id=agent_id, user_id=current_user.id, data=data)


@router.post("/agents/{agent_id}/toggle", response_model=AgentResponse)
async def toggle_agent(
    agent_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> AgentResponse:
    service = _get_service(db)
    return await service.toggle_agent(agent_id=agent_id, user_id=current_user.id)


@router.get("/agents/{agent_id}/runs", response_model=AgentRunList)
async def get_agent_runs(
    agent_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AgentRunList:
    service = _get_service(db)
    return await service.get_agent_runs(agent_id=agent_id, user_id=current_user.id, page=page, page_size=page_size)


@router.get("/agents/{agent_id}/memory", response_model=list[AgentMemoryResponse])
async def get_agent_memory(
    agent_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> list[AgentMemoryResponse]:
    service = _get_service(db)
    return await service.get_agent_memory(agent_id=agent_id, user_id=current_user.id)


@router.post("/agents/{agent_id}/memory", response_model=AgentMemoryResponse, status_code=201)
async def add_agent_memory(
    agent_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    key: str = Query(..., max_length=255),
    value: str = Query(...),
    memory_type: str = Query("fact"),
) -> AgentMemoryResponse:
    service = _get_service(db)
    return await service.add_agent_memory(agent_id=agent_id, user_id=current_user.id, key=key, value=value, memory_type=memory_type)


@router.delete("/agents/{agent_id}/memory/{memory_id}", status_code=204)
async def delete_agent_memory(
    agent_id: uuid.UUID,
    memory_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    service = _get_service(db)
    await service.delete_agent_memory(agent_id=agent_id, memory_id=memory_id, user_id=current_user.id)


@router.get("/agents/{agent_id}/tools", response_model=list[AgentToolResponse])
async def get_agent_tools(
    agent_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> list[AgentToolResponse]:
    service = _get_service(db)
    return await service.get_agent_tools(agent_id=agent_id, user_id=current_user.id)


@router.post("/agents/{agent_id}/tools", response_model=AgentToolResponse, status_code=201)
async def set_agent_tool(
    agent_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    tool_name: str = Query(..., max_length=100),
    enabled: bool = Query(True),
) -> AgentToolResponse:
    service = _get_service(db)
    return await service.set_agent_tool(agent_id=agent_id, user_id=current_user.id, tool_name=tool_name, enabled=enabled)


@router.post("/agents/{agent_id}/chat")
async def agent_chat(
    agent_id: uuid.UUID,
    data: AgentChatRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    service = _get_service(db)
    return await service.send_agent_message(
        agent_id=agent_id,
        user_id=current_user.id,
        message=data.message,
        conversation_id=data.conversation_id,
    )


@router.get("/providers")
async def list_providers(
    current_user: CurrentUser,
    db: DbSession,
) -> list[dict]:
    service = _get_service(db)
    return await service.get_agent_providers()


@router.get("/tools")
async def list_tools(
    current_user: CurrentUser,
    db: DbSession,
) -> list[dict]:
    service = _get_service(db)
    return await service.get_available_tools()
