"""
Workflow Events package.

Provides the event types and event bus for workflow progress notifications.
"""

from app.workflows.events.workflow_events import WorkflowEvent, WorkflowEventBus

__all__ = ["WorkflowEvent", "WorkflowEventBus"]
