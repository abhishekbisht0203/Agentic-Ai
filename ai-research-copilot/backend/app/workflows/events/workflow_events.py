"""
Workflow Events and Event Bus.

Provides a lightweight publish/subscribe event system for broadcasting
workflow progress notifications. Subscribers can register for specific
event types (e.g. ``step_started``, ``step_completed``) or all events.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


@dataclass
class WorkflowEvent:
    """Represents a single workflow lifecycle event.

    Attributes:
        event_type: The type of event (e.g. ``step_started``, ``workflow_completed``).
        execution_id: The UUID of the workflow execution this event relates to.
        data: Arbitrary event payload.
        timestamp: UTC timestamp when the event was created.
        step_name: Optional name of the step the event relates to.
        workflow_id: Optional UUID of the workflow definition.
    """

    event_type: str
    execution_id: uuid.UUID
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    step_name: str | None = None
    workflow_id: uuid.UUID | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to a JSON-compatible dictionary.

        Returns:
            A dictionary representation suitable for logging or transport.
        """
        return {
            "event_type": self.event_type,
            "execution_id": str(self.execution_id),
            "workflow_id": str(self.workflow_id) if self.workflow_id else None,
            "step_name": self.step_name,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


# Type alias for subscriber callbacks – may be sync or async
SubscriberCallback = Callable[[WorkflowEvent], Any] | Callable[[WorkflowEvent], Awaitable[Any]]


class WorkflowEventBus:
    """Publish/subscribe event bus for workflow lifecycle events.

    Subscribers register for specific event types or ``"*"`` to receive
    all events. Callbacks may be synchronous or asynchronous – async
    callbacks are awaited automatically.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[SubscriberCallback]] = {}
        self._event_history: list[WorkflowEvent] = []
        self._max_history: int = 1000

    def subscribe(self, event_type: str, callback: SubscriberCallback) -> None:
        """Register a callback for a specific event type.

        Use ``event_type="*"`` to subscribe to all events.

        Args:
            event_type: The event type to listen for.
            callback: The callable to invoke when the event fires.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            logger.debug(
                "Subscriber registered for event '%s': %s",
                event_type,
                callback.__qualname__,
            )

    def unsubscribe(self, event_type: str, callback: SubscriberCallback) -> bool:
        """Remove a previously registered callback.

        Args:
            event_type: The event type the callback was registered for.
            callback: The callback to remove.

        Returns:
            True if the callback was found and removed.
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                return True
            except ValueError:
                pass
        return False

    def unsubscribe_all(self, event_type: str | None = None) -> int:
        """Remove all subscribers, optionally for a specific event type.

        Args:
            event_type: If provided, only remove subscribers for this type.
                        If None, remove all subscribers.

        Returns:
            The number of subscribers removed.
        """
        count = 0
        if event_type:
            count = len(self._subscribers.pop(event_type, []))
        else:
            count = sum(len(subs) for subs in self._subscribers.values())
            self._subscribers.clear()
        logger.debug("Removed %d subscribers", count)
        return count

    async def publish(self, event: WorkflowEvent) -> dict[str, Any]:
        """Publish an event to all matching subscribers.

        Dispatches the event to subscribers registered for the event's
        type and to wildcard (``"*"``) subscribers. Async callbacks are
        awaited; sync callbacks are called directly.

        Args:
            event: The WorkflowEvent to publish.

        Returns:
            A summary dictionary with ``delivered`` count and any errors.
        """
        self._record_history(event)

        callbacks = list(self._subscribers.get(event.event_type, []))
        wildcard_callbacks = list(self._subscribers.get("*", []))
        all_callbacks = callbacks + wildcard_callbacks

        if not all_callbacks:
            logger.debug(
                "No subscribers for event '%s' (execution=%s)",
                event.event_type,
                event.execution_id,
            )
            return {"delivered": 0, "errors": []}

        delivered = 0
        errors: list[dict[str, Any]] = []

        for callback in all_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
                delivered += 1
            except Exception as exc:
                logger.exception(
                    "Subscriber %s failed for event '%s'",
                    callback.__qualname__,
                    event.event_type,
                )
                errors.append(
                    {
                        "subscriber": callback.__qualname__,
                        "error": str(exc),
                    }
                )

        logger.debug(
            "Published event '%s' to %d/%d subscribers (execution=%s)",
            event.event_type,
            delivered,
            len(all_callbacks),
            event.execution_id,
        )

        return {"delivered": delivered, "errors": errors}

    def get_subscriber_count(self, event_type: str | None = None) -> int:
        """Count registered subscribers.

        Args:
            event_type: If provided, count only subscribers for this type.

        Returns:
            The number of registered subscribers.
        """
        if event_type:
            return len(self._subscribers.get(event_type, []))
        return sum(len(subs) for subs in self._subscribers.values())

    def get_event_types(self) -> list[str]:
        """Return a list of event types that have at least one subscriber.

        Returns:
            Sorted list of event type strings.
        """
        return sorted(self._subscribers.keys())

    def get_history(
        self,
        execution_id: uuid.UUID | None = None,
        event_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Retrieve recent event history.

        Args:
            execution_id: Optional filter by execution UUID.
            event_type: Optional filter by event type.
            limit: Maximum number of events to return.

        Returns:
            A list of event dictionaries in chronological order.
        """
        events = self._event_history

        if execution_id:
            events = [e for e in events if e.execution_id == execution_id]
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return [e.to_dict() for e in events[-limit:]]

    def clear_history(self) -> int:
        """Clear the event history buffer.

        Returns:
            The number of events removed.
        """
        count = len(self._event_history)
        self._event_history.clear()
        return count

    def _record_history(self, event: WorkflowEvent) -> None:
        """Add an event to the history buffer, evicting old entries.

        Args:
            event: The event to record.
        """
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history :]

    # ------------------------------------------------------------------
    # Convenience factories for common event types
    # ------------------------------------------------------------------

    @staticmethod
    def workflow_started(
        execution_id: uuid.UUID,
        workflow_id: uuid.UUID | None = None,
        data: dict[str, Any] | None = None,
    ) -> WorkflowEvent:
        """Create a ``workflow_started`` event.

        Args:
            execution_id: The execution UUID.
            workflow_id: The workflow definition UUID.
            data: Optional additional payload.

        Returns:
            A WorkflowEvent instance.
        """
        return WorkflowEvent(
            event_type="workflow_started",
            execution_id=execution_id,
            workflow_id=workflow_id,
            data=data or {},
        )

    @staticmethod
    def step_started(
        execution_id: uuid.UUID,
        step_name: str,
        workflow_id: uuid.UUID | None = None,
        data: dict[str, Any] | None = None,
    ) -> WorkflowEvent:
        """Create a ``step_started`` event.

        Args:
            execution_id: The execution UUID.
            step_name: The name of the step that started.
            workflow_id: The workflow definition UUID.
            data: Optional additional payload.

        Returns:
            A WorkflowEvent instance.
        """
        return WorkflowEvent(
            event_type="step_started",
            execution_id=execution_id,
            workflow_id=workflow_id,
            step_name=step_name,
            data=data or {},
        )

    @staticmethod
    def step_completed(
        execution_id: uuid.UUID,
        step_name: str,
        result: Any = None,
        duration_ms: int = 0,
        workflow_id: uuid.UUID | None = None,
    ) -> WorkflowEvent:
        """Create a ``step_completed`` event.

        Args:
            execution_id: The execution UUID.
            step_name: The name of the completed step.
            result: The step's output.
            duration_ms: Wall-clock execution time in milliseconds.
            workflow_id: The workflow definition UUID.

        Returns:
            A WorkflowEvent instance.
        """
        return WorkflowEvent(
            event_type="step_completed",
            execution_id=execution_id,
            workflow_id=workflow_id,
            step_name=step_name,
            data={"result": result, "duration_ms": duration_ms},
        )

    @staticmethod
    def step_failed(
        execution_id: uuid.UUID,
        step_name: str,
        error: str,
        workflow_id: uuid.UUID | None = None,
    ) -> WorkflowEvent:
        """Create a ``step_failed`` event.

        Args:
            execution_id: The execution UUID.
            step_name: The name of the failed step.
            error: Description of the failure.
            workflow_id: The workflow definition UUID.

        Returns:
            A WorkflowEvent instance.
        """
        return WorkflowEvent(
            event_type="step_failed",
            execution_id=execution_id,
            workflow_id=workflow_id,
            step_name=step_name,
            data={"error": error},
        )

    @staticmethod
    def workflow_completed(
        execution_id: uuid.UUID,
        output_data: dict[str, Any] | None = None,
        duration_ms: int = 0,
        workflow_id: uuid.UUID | None = None,
    ) -> WorkflowEvent:
        """Create a ``workflow_completed`` event.

        Args:
            execution_id: The execution UUID.
            output_data: The aggregated workflow output.
            duration_ms: Total execution time in milliseconds.
            workflow_id: The workflow definition UUID.

        Returns:
            A WorkflowEvent instance.
        """
        return WorkflowEvent(
            event_type="workflow_completed",
            execution_id=execution_id,
            workflow_id=workflow_id,
            data={"output_data": output_data or {}, "duration_ms": duration_ms},
        )

    @staticmethod
    def workflow_failed(
        execution_id: uuid.UUID,
        error: str,
        workflow_id: uuid.UUID | None = None,
    ) -> WorkflowEvent:
        """Create a ``workflow_failed`` event.

        Args:
            execution_id: The execution UUID.
            error: Description of the failure.
            workflow_id: The workflow definition UUID.

        Returns:
            A WorkflowEvent instance.
        """
        return WorkflowEvent(
            event_type="workflow_failed",
            execution_id=execution_id,
            workflow_id=workflow_id,
            data={"error": error},
        )

    @staticmethod
    def workflow_cancelled(
        execution_id: uuid.UUID,
        workflow_id: uuid.UUID | None = None,
    ) -> WorkflowEvent:
        """Create a ``workflow_cancelled`` event.

        Args:
            execution_id: The execution UUID.
            workflow_id: The workflow definition UUID.

        Returns:
            A WorkflowEvent instance.
        """
        return WorkflowEvent(
            event_type="workflow_cancelled",
            execution_id=execution_id,
            workflow_id=workflow_id,
            data={},
        )
