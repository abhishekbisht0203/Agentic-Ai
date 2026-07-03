"""
AI Agents package.

Exposes every agent class and the orchestrator for convenient imports::

    from app.agents import (
        BaseAgent,
        SupervisorAgent,
        ResearchAgent,
        PlannerAgent,
        DataAnalystAgent,
        CriticAgent,
        CodeAssistantAgent,
        AutomationAgent,
        DocumentQAAgent,
        MemoryAgent,
        AIOrchestrator,
    )
"""

from app.agents.base.agent import BaseAgent
from app.agents.supervisor.supervisor import SupervisorAgent
from app.agents.research.research_agent import ResearchAgent
from app.agents.planner.planner import PlannerAgent
from app.agents.data_analyst.data_analyst_agent import DataAnalystAgent
from app.agents.critic.critic_agent import CriticAgent
from app.agents.code_assistant.code_assistant_agent import CodeAssistantAgent
from app.agents.automation.automation_agent import AutomationAgent
from app.agents.document_qa.document_qa_agent import DocumentQAAgent
from app.agents.memory.memory_agent import MemoryAgent
from app.agents.orchestrator.orchestrator import AIOrchestrator

__all__ = [
    "BaseAgent",
    "SupervisorAgent",
    "ResearchAgent",
    "PlannerAgent",
    "DataAnalystAgent",
    "CriticAgent",
    "CodeAssistantAgent",
    "AutomationAgent",
    "DocumentQAAgent",
    "MemoryAgent",
    "AIOrchestrator",
]
