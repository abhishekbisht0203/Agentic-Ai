"""Workflow service for CRUD, execution, and monitoring."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError, WorkflowError
from app.models.workflow import (
    ExecutionStatus,
    Workflow,
    WorkflowExecution,
    WorkflowStatus,
)
from app.repositories.workflow import WorkflowRepository
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

logger = logging.getLogger(__name__)


class WorkflowExecutionRepository:
    """Repository for WorkflowExecution model operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, execution_id: uuid.UUID) -> WorkflowExecution | None:
        return await self.db.get(WorkflowExecution, execution_id)

    async def create(self, **kwargs) -> WorkflowExecution:
        instance = WorkflowExecution(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, execution_id: uuid.UUID, **kwargs) -> WorkflowExecution | None:
        instance = await self.get_by_id(execution_id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await self.db.flush()
            await self.db.refresh(instance)
        return instance

    async def get_by_workflow(
        self, workflow_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[WorkflowExecution], int]:
        query = (
            select(WorkflowExecution)
            .where(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.is_deleted == False,
            )
            .order_by(WorkflowExecution.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        count_query = (
            select(func.count())
            .select_from(WorkflowExecution)
            .where(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.is_deleted == False,
            )
        )
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar() or 0

    async def cancel_execution(self, execution_id: uuid.UUID) -> WorkflowExecution | None:
        instance = await self.get_by_id(execution_id)
        if instance and instance.status in (
            ExecutionStatus.PENDING,
            ExecutionStatus.RUNNING,
            ExecutionStatus.WAITING_APPROVAL,
        ):
            instance.status = ExecutionStatus.CANCELLED
            instance.completed_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(instance)
            return instance
        return None


class WorkflowService:
    """Service for workflow CRUD, execution, and monitoring."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.workflow_repo = WorkflowRepository(db)
        self.execution_repo = WorkflowExecutionRepository(db)

    async def create_workflow(
        self, user_id: uuid.UUID, data: WorkflowCreate
    ) -> WorkflowResponse:
        """Create a new workflow.

        Args:
            user_id: UUID of the owning user.
            data: Validated workflow creation payload.

        Returns:
            WorkflowResponse with the created workflow data.
        """
        workflow = await self.workflow_repo.create(
            user_id=user_id,
            name=data.name,
            description=data.description,
            workflow_type=data.workflow_type,
            definition=data.definition,
            is_template=data.is_template,
        )
        logger.info(
            "Workflow created: id=%s name=%s user=%s",
            workflow.id,
            workflow.name,
            user_id,
        )
        return WorkflowResponse.model_validate(workflow)

    async def get_workflow(
        self, workflow_id: uuid.UUID, user_id: uuid.UUID
    ) -> WorkflowDetail:
        """Retrieve full details for a single workflow.

        Args:
            workflow_id: UUID of the workflow.
            user_id: UUID of the owning user.

        Raises:
            NotFoundError: If the workflow does not exist or is not owned by the user.
        """
        workflow = await self._get_owned_workflow(workflow_id, user_id)
        return WorkflowDetail.model_validate(workflow)

    async def list_workflows(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> WorkflowList:
        """Return a paginated list of the user's workflows.

        Args:
            user_id: UUID of the owning user.
            page: 1-indexed page number.
            page_size: Number of items per page (max 100).
        """
        page_size = min(page_size, 100)
        skip = (page - 1) * page_size
        items, total = await self.workflow_repo.get_by_user(user_id, skip, page_size)
        return WorkflowList(
            items=[WorkflowResponse.model_validate(w) for w in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_workflow(
        self,
        workflow_id: uuid.UUID,
        user_id: uuid.UUID,
        data: WorkflowUpdate,
    ) -> WorkflowResponse:
        """Update workflow metadata.

        Args:
            workflow_id: UUID of the workflow.
            user_id: UUID of the owning user.
            data: Fields to update.

        Raises:
            NotFoundError: If the workflow does not exist or is not owned by the user.
            ValidationError: If no update fields are provided.
        """
        await self._get_owned_workflow(workflow_id, user_id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError(message="No fields provided for update")

        if "name" in update_data:
            name = update_data["name"].strip() if isinstance(update_data["name"], str) else update_data["name"]
            if not name:
                raise ValidationError(message="Workflow name cannot be empty")
            update_data["name"] = name

        updated = await self.workflow_repo.update(workflow_id, **update_data)
        return WorkflowResponse.model_validate(updated)

    async def delete_workflow(
        self, workflow_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Soft-delete a workflow.

        Args:
            workflow_id: UUID of the workflow.
            user_id: UUID of the owning user.

        Raises:
            NotFoundError: If the workflow does not exist or is not owned by the user.
        """
        await self._get_owned_workflow(workflow_id, user_id)
        await self.workflow_repo.delete(workflow_id)
        logger.info("Workflow deleted: id=%s user=%s", workflow_id, user_id)

    async def execute_workflow(
        self,
        workflow_id: uuid.UUID,
        user_id: uuid.UUID,
        data: WorkflowExecuteRequest,
    ) -> WorkflowExecutionResponse:
        """Start a new workflow execution.

        Creates a WorkflowExecution record in PENDING status. The actual
        orchestration is handled by a background worker (Celery) which will
        transition the execution to RUNNING and process each step.

        Args:
            workflow_id: UUID of the workflow to execute.
            user_id: UUID of the user initiating execution.
            data: Optional input data for the execution.

        Raises:
            NotFoundError: If the workflow does not exist or is not owned by the user.
            WorkflowError: If the workflow is not in ACTIVE status.
        """
        workflow = await self._get_owned_workflow(workflow_id, user_id)

        if workflow.status != WorkflowStatus.ACTIVE:
            raise WorkflowError(
                message="Only active workflows can be executed",
                details={
                    "workflow_id": str(workflow_id),
                    "current_status": workflow.status,
                },
            )

        execution = await self.execution_repo.create(
            workflow_id=workflow_id,
            user_id=user_id,
            status=ExecutionStatus.PENDING,
            input_data=data.input_data,
            progress=0.0,
        )

        await self.workflow_repo.update(
            workflow_id,
            execution_count=workflow.execution_count + 1,
            last_executed_at=datetime.now(timezone.utc),
        )

        logger.info(
            "Workflow execution started: execution_id=%s workflow_id=%s user=%s",
            execution.id,
            workflow_id,
            user_id,
        )
        return WorkflowExecutionResponse.model_validate(execution)

    async def get_execution(
        self, execution_id: uuid.UUID, user_id: uuid.UUID
    ) -> WorkflowExecutionResponse:
        """Retrieve details for a single workflow execution.

        Args:
            execution_id: UUID of the execution.
            user_id: UUID of the user who initiated the execution.

        Raises:
            NotFoundError: If the execution does not exist or does not belong to the user.
        """
        execution = await self._get_owned_execution(execution_id, user_id)
        return WorkflowExecutionResponse.model_validate(execution)

    async def list_executions(
        self,
        workflow_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> WorkflowExecutionList:
        """Return a paginated list of executions for a workflow.

        Args:
            workflow_id: UUID of the workflow.
            user_id: UUID of the owning user.
            page: 1-indexed page number.
            page_size: Number of items per page (max 100).

        Raises:
            NotFoundError: If the workflow does not exist or is not owned by the user.
        """
        await self._get_owned_workflow(workflow_id, user_id)

        page_size = min(page_size, 100)
        skip = (page - 1) * page_size
        items, total = await self.execution_repo.get_by_workflow(
            workflow_id, skip, page_size
        )
        return WorkflowExecutionList(
            items=[WorkflowExecutionResponse.model_validate(e) for e in items],
            total=total,
        )

    async def cancel_execution(
        self, execution_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Cancel a pending or running workflow execution.

        Only executions in PENDING, RUNNING, or WAITING_APPROVAL status
        can be cancelled. Terminal states (COMPLETED, FAILED, CANCELLED)
        are rejected.

        Args:
            execution_id: UUID of the execution to cancel.
            user_id: UUID of the user who initiated the execution.

        Raises:
            NotFoundError: If the execution does not exist or does not belong to the user.
            WorkflowError: If the execution is in a terminal state.
        """
        execution = await self._get_owned_execution(execution_id, user_id)

        terminal_states = {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        }
        if execution.status in terminal_states:
            raise WorkflowError(
                message="Cannot cancel execution in terminal state",
                details={
                    "execution_id": str(execution_id),
                    "current_status": execution.status,
                },
            )

        cancelled = await self.execution_repo.cancel_execution(execution_id)
        if not cancelled:
            raise WorkflowError(
                message="Failed to cancel execution",
                details={"execution_id": str(execution_id)},
            )

        logger.info(
            "Workflow execution cancelled: execution_id=%s user=%s",
            execution_id,
            user_id,
        )

    async def _get_owned_workflow(
        self, workflow_id: uuid.UUID, user_id: uuid.UUID
    ) -> Workflow:
        """Fetch a workflow and verify ownership.

        Raises:
            NotFoundError: If the workflow is missing or belongs to another user.
        """
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow or workflow.user_id != user_id:
            raise NotFoundError(message="Workflow not found")
        return workflow

    async def _get_owned_execution(
        self, execution_id: uuid.UUID, user_id: uuid.UUID
    ) -> WorkflowExecution:
        """Fetch an execution and verify ownership.

        Raises:
            NotFoundError: If the execution is missing or belongs to another user.
        """
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution or execution.user_id != user_id:
            raise NotFoundError(message="Workflow execution not found")
        return execution
