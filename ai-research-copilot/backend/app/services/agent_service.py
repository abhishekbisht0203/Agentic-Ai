"""Agent configuration and execution service."""

import logging
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.workflow import AgentConfiguration, Task, TaskStatus, TaskType
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

logger = logging.getLogger(__name__)


class AgentConfigurationRepository:
    """Repository for AgentConfiguration model operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, config_id: uuid.UUID) -> AgentConfiguration | None:
        return await self.db.get(AgentConfiguration, config_id)

    async def get_by_agent_type(self, agent_type: str) -> AgentConfiguration | None:
        query = select(AgentConfiguration).where(
            AgentConfiguration.agent_type == agent_type,
            AgentConfiguration.is_deleted == False,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> AgentConfiguration:
        instance = AgentConfiguration(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, config_id: uuid.UUID, **kwargs) -> AgentConfiguration | None:
        instance = await self.get_by_id(config_id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await self.db.flush()
            await self.db.refresh(instance)
        return instance

    async def delete(self, config_id: uuid.UUID) -> bool:
        instance = await self.get_by_id(config_id)
        if instance:
            instance.is_deleted = True
            await self.db.flush()
            return True
        return False

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[AgentConfiguration], int]:
        query = (
            select(AgentConfiguration)
            .where(AgentConfiguration.is_deleted == False)
            .order_by(AgentConfiguration.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        count_query = (
            select(func.count())
            .select_from(AgentConfiguration)
            .where(AgentConfiguration.is_deleted == False)
        )
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar() or 0


class TaskRepository:
    """Repository for Task model operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, task_id: uuid.UUID) -> Task | None:
        return await self.db.get(Task, task_id)

    async def create(self, **kwargs) -> Task:
        instance = Task(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, task_id: uuid.UUID, **kwargs) -> Task | None:
        instance = await self.get_by_id(task_id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await self.db.flush()
            await self.db.refresh(instance)
        return instance


class AgentService:
    """Service for agent configuration CRUD and agent execution."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.agent_repo = AgentConfigurationRepository(db)
        self.task_repo = TaskRepository(db)

    async def create_agent_config(
        self, data: AgentConfigurationCreate
    ) -> AgentConfigurationResponse:
        """Create a new agent configuration.

        Args:
            data: Validated agent configuration creation payload.

        Raises:
            ValidationError: If an agent with the same agent_type already exists.

        Returns:
            AgentConfigurationResponse with the created configuration data.
        """
        existing = await self.agent_repo.get_by_agent_type(data.agent_type)
        if existing:
            raise ValidationError(
                message=f"Agent configuration with type '{data.agent_type}' already exists",
                details={"agent_type": data.agent_type},
            )

        config = await self.agent_repo.create(
            name=data.name,
            agent_type=data.agent_type,
            description=data.description,
            system_prompt=data.system_prompt,
            model=data.model,
            temperature=data.temperature if data.temperature is not None else 0.7,
            max_tokens=data.max_tokens if data.max_tokens is not None else 4096,
            tools=data.tools,
            is_active=data.is_active if data.is_active is not None else True,
        )
        logger.info(
            "Agent configuration created: id=%s agent_type=%s",
            config.id,
            config.agent_type,
        )
        return AgentConfigurationResponse.model_validate(config)

    async def get_agent_config(
        self, config_id: uuid.UUID
    ) -> AgentConfigurationDetail:
        """Retrieve full details for a single agent configuration.

        Args:
            config_id: UUID of the agent configuration.

        Raises:
            NotFoundError: If the configuration does not exist.
        """
        config = await self._get_config_or_raise(config_id)
        return AgentConfigurationDetail.model_validate(config)

    async def list_agent_configs(
        self, page: int = 1, page_size: int = 100
    ) -> AgentConfigurationList:
        """Return a paginated list of agent configurations.

        Args:
            page: 1-indexed page number.
            page_size: Number of items per page (max 100).
        """
        page_size = min(page_size, 100)
        skip = (page - 1) * page_size
        items, total = await self.agent_repo.get_all(skip, page_size)
        return AgentConfigurationList(
            items=[AgentConfigurationResponse.model_validate(c) for c in items],
            total=total,
        )

    async def update_agent_config(
        self, config_id: uuid.UUID, data: AgentConfigurationUpdate
    ) -> AgentConfigurationResponse:
        """Update an agent configuration.

        Args:
            config_id: UUID of the agent configuration.
            data: Fields to update.

        Raises:
            NotFoundError: If the configuration does not exist.
            ValidationError: If no update fields are provided, or if the
                new agent_type conflicts with an existing configuration.
        """
        await self._get_config_or_raise(config_id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError(message="No fields provided for update")

        if "name" in update_data:
            name = update_data["name"].strip() if isinstance(update_data["name"], str) else update_data["name"]
            if not name:
                raise ValidationError(message="Agent name cannot be empty")
            update_data["name"] = name

        if "agent_type" in update_data:
            new_type = update_data["agent_type"]
            existing = await self.agent_repo.get_by_agent_type(new_type)
            if existing and existing.id != config_id:
                raise ValidationError(
                    message=f"Agent configuration with type '{new_type}' already exists",
                    details={"agent_type": new_type},
                )

        updated = await self.agent_repo.update(config_id, **update_data)
        return AgentConfigurationResponse.model_validate(updated)

    async def delete_agent_config(self, config_id: uuid.UUID) -> None:
        """Soft-delete an agent configuration.

        Args:
            config_id: UUID of the agent configuration.

        Raises:
            NotFoundError: If the configuration does not exist.
        """
        await self._get_config_or_raise(config_id)
        await self.agent_repo.delete(config_id)
        logger.info("Agent configuration deleted: id=%s", config_id)

    async def execute_agent(
        self, user_id: uuid.UUID, data: AgentExecuteRequest
    ) -> AgentExecuteResponse:
        """Execute an agent task asynchronously.

        Validates that the requested agent type exists and is active,
        then creates a Task record in PENDING status. The actual agent
        execution is performed by a Celery worker.

        Args:
            user_id: UUID of the user initiating the execution.
            data: Validated agent execution request.

        Raises:
            NotFoundError: If no active agent configuration matches the type.

        Returns:
            AgentExecuteResponse with the created task data.
        """
        config = await self.agent_repo.get_by_agent_type(data.agent_type)
        if not config or not config.is_active:
            raise NotFoundError(
                message=f"Active agent configuration not found for type '{data.agent_type}'",
                details={"agent_type": data.agent_type},
            )

        input_data = {
            "agent_type": data.agent_type,
            "agent_config_id": str(config.id),
            "input_data": data.input_data,
            "conversation_id": str(data.conversation_id) if data.conversation_id else None,
            "model": data.model or config.model,
            "system_prompt": config.system_prompt,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "tools": config.tools,
        }

        task = await self.task_repo.create(
            user_id=user_id,
            task_type=TaskType.AGENT,
            status=TaskStatus.PENDING,
            priority=0,
            input_data=input_data,
        )

        logger.info(
            "Agent task created: task_id=%s agent_type=%s user=%s",
            task.id,
            data.agent_type,
            user_id,
        )

        return AgentExecuteResponse(
            id=task.id,
            agent_type=data.agent_type,
            status=task.status,
            output_data=task.output_data,
            error_message=task.error_message,
            execution_time_ms=None,
        )

    async def get_agent_status(self, task_id: uuid.UUID) -> TaskResponse:
        """Retrieve the status of an agent execution task.

        Args:
            task_id: UUID of the background task.

        Raises:
            NotFoundError: If the task does not exist.
        """
        task = await self._get_task_or_raise(task_id)
        return TaskResponse.model_validate(task)

    async def _get_config_or_raise(
        self, config_id: uuid.UUID
    ) -> AgentConfiguration:
        """Fetch an agent configuration or raise NotFoundError."""
        config = await self.agent_repo.get_by_id(config_id)
        if not config:
            raise NotFoundError(message="Agent configuration not found")
        return config

    async def _get_task_or_raise(self, task_id: uuid.UUID) -> Task:
        """Fetch a task or raise NotFoundError."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError(message="Task not found")
        return task
