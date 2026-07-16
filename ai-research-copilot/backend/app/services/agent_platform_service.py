
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.agent import Agent, AgentMemory, AgentRun, AgentTool
from app.models.conversation import Conversation, Message
from app.models.document import KnowledgeBase
from app.schemas.agent_platform import (
    AgentCreate,
    AgentDuplicate,
    AgentList,
    AgentMemoryResponse,
    AgentResponse,
    AgentRunList,
    AgentRunResponse,
    AgentToolResponse,
    AgentUpdate,
    AgentWithStats,
)
from app.services.usage_tracking_service import UsageTrackingService

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPTS: dict[str, str] = {
    "planner": """You are a Planner Agent. Your role is to break complex problems into actionable, step-by-step plans.
Analyze the user's goal, identify dependencies, estimate effort, and produce a clear roadmap.
Always structure your response with: Goal, Steps (numbered), Dependencies, Estimated effort.""",
    "research": """You are a Research Agent. Your role is to find, evaluate, and synthesize information.
When given a topic, produce a well-structured research summary with key findings, sources, and open questions.
Be thorough, cite sources, and distinguish between verified facts and inferences.""",
    "code_assistant": """You are a Code Assistant Agent. You write, explain, debug, and review code.
Follow best practices, use clear variable names, add minimal comments, and handle edge cases.
When debugging, first identify the issue, then provide the fix with explanation.""",
    "document_qa": """You are a Document Q&A Agent. You answer questions based on uploaded documents.
Use the provided context to give accurate answers. If the answer isn't in the documents, say so clearly.
Cite specific parts of the source material when possible.""",
    "automation": """You are an Automation Agent. You design workflows and automate repetitive tasks.
Break down processes into steps, identify automation opportunities, and design efficient pipelines.
Consider error handling, retries, and monitoring in your designs.""",
    "memory": """You are a Memory Agent. You store, organize, and recall user context and preferences.
Keep track of important facts, user preferences, and conversation history.
Provide relevant context when previous information is referenced.""",
    "critic": """You are a Critic Agent. You review responses and identify weaknesses, gaps, and improvements.
Analyze arguments for logical consistency, evidence quality, and completeness.
Provide constructive feedback with specific suggestions for improvement.""",
    "data_analyst": """You are a Data Analyst Agent. You analyze data from CSV, Excel, JSON and other formats.
Identify trends, patterns, anomalies, and insights. Present findings with visual descriptions.
Support conclusions with statistical evidence when possible.""",
    "general": """You are a General Assistant Agent. You help with a wide range of tasks.
Be helpful, accurate, and concise. When unsure, ask clarifying questions.
Follow instructions carefully and provide complete, well-structured responses.""",
}


class AgentPlatformRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, agent_id: uuid.UUID) -> Agent | None:
        return await self.db.get(Agent, agent_id)

    async def create(self, **kwargs) -> Agent:
        instance = Agent(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, agent_id: uuid.UUID, **kwargs) -> Agent | None:
        instance = await self.get_by_id(agent_id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await self.db.flush()
            await self.db.refresh(instance)
        return instance

    async def delete(self, agent_id: uuid.UUID) -> bool:
        instance = await self.get_by_id(agent_id)
        if instance:
            instance.is_deleted = True
            await self.db.flush()
            return True
        return False

    async def get_all(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> tuple[list[Agent], int]:
        conditions = [Agent.user_id == user_id, Agent.is_deleted == False]
        if search:
            like = f"%{search}%"
            conditions.append(
                or_(
                    Agent.name.ilike(like),
                    Agent.description.ilike(like),
                    Agent.model.ilike(like),
                    Agent.provider.ilike(like),
                )
            )
        query = (
            select(Agent)
            .where(*conditions)
            .order_by(Agent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        count_query = select(func.count()).select_from(Agent).where(*conditions)
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        return list(result.scalars().all()), count_result.scalar() or 0


class AgentPlatformService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AgentPlatformRepository(db)
        self.usage_tracker = UsageTrackingService(db)

    async def create_agent(self, user_id: uuid.UUID, data: AgentCreate) -> AgentResponse:
        config = await self.repo.create(
            user_id=user_id,
            name=data.name,
            description=data.description,
            system_prompt=data.system_prompt,
            avatar=data.avatar,
            icon=data.icon,
            color=data.color,
            model=data.model,
            provider=data.provider,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            top_p=data.top_p,
            frequency_penalty=data.frequency_penalty,
            presence_penalty=data.presence_penalty,
            tools_enabled=data.tools_enabled,
            knowledge_base_id=data.knowledge_base_id,
            memory_enabled=data.memory_enabled,
            rag_enabled=data.rag_enabled,
            workflow_enabled=data.workflow_enabled,
            status=data.status,
            visibility=data.visibility,
        )
        logger.info("Agent created: id=%s name=%s user=%s", config.id, config.name, user_id)
        return AgentResponse.model_validate(config)

    async def get_agent(self, agent_id: uuid.UUID, user_id: uuid.UUID) -> AgentWithStats:
        agent = await self._get_agent_or_raise(agent_id, user_id)
        stats = await self._get_agent_stats(agent_id, user_id)
        result = AgentWithStats.model_validate(agent)
        for k, v in stats.items():
            setattr(result, k, v)
        return result

    async def list_agents(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 100,
        search: str | None = None,
    ) -> AgentList:
        page_size = min(page_size, 100)
        skip = (page - 1) * page_size
        items, total = await self.repo.get_all(user_id, skip, page_size, search)
        agents_with_stats = []
        for agent in items:
            stats = await self._get_agent_stats(agent.id, user_id)
            aws = AgentWithStats.model_validate(agent)
            for k, v in stats.items():
                setattr(aws, k, v)
            agents_with_stats.append(aws)
        return AgentList(items=agents_with_stats, total=total)

    async def update_agent(self, agent_id: uuid.UUID, user_id: uuid.UUID, data: AgentUpdate) -> AgentResponse:
        await self._get_agent_or_raise(agent_id, user_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError(message="No fields provided for update")
        if "name" in update_data:
            name = update_data["name"].strip()
            if not name:
                raise ValidationError(message="Agent name cannot be empty")
            update_data["name"] = name
        updated = await self.repo.update(agent_id, **update_data)
        return AgentResponse.model_validate(updated)

    async def delete_agent(self, agent_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self._get_agent_or_raise(agent_id, user_id)
        await self.repo.delete(agent_id)
        logger.info("Agent deleted: id=%s user=%s", agent_id, user_id)

    async def duplicate_agent(self, agent_id: uuid.UUID, user_id: uuid.UUID, data: AgentDuplicate) -> AgentResponse:
        original = await self._get_agent_or_raise(agent_id, user_id)
        dup_data = AgentCreate(
            name=data.name or f"{original.name} (copy)",
            description=original.description,
            system_prompt=original.system_prompt,
            avatar=original.avatar,
            icon=original.icon,
            color=original.color,
            model=original.model,
            provider=original.provider,
            temperature=original.temperature,
            max_tokens=original.max_tokens,
            top_p=original.top_p,
            frequency_penalty=original.frequency_penalty,
            presence_penalty=original.presence_penalty,
            tools_enabled=original.tools_enabled,
            knowledge_base_id=original.knowledge_base_id,
            memory_enabled=original.memory_enabled,
            rag_enabled=original.rag_enabled,
            workflow_enabled=original.workflow_enabled,
            status="inactive",
            visibility=original.visibility,
        )
        return await self.create_agent(user_id, dup_data)

    async def toggle_agent(self, agent_id: uuid.UUID, user_id: uuid.UUID) -> AgentResponse:
        agent = await self._get_agent_or_raise(agent_id, user_id)
        new_status = "inactive" if agent.status == "active" else "active"
        updated = await self.repo.update(agent_id, status=new_status)
        return AgentResponse.model_validate(updated)

    async def get_agent_runs(
        self,
        agent_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> AgentRunList:
        await self._get_agent_or_raise(agent_id, user_id)
        page_size = min(page_size, 100)
        skip = (page - 1) * page_size
        query = (
            select(AgentRun)
            .where(AgentRun.agent_id == agent_id, AgentRun.is_deleted == False)
            .order_by(AgentRun.created_at.desc())
            .offset(skip)
            .limit(page_size)
        )
        count_q = select(func.count()).select_from(AgentRun).where(AgentRun.agent_id == agent_id, AgentRun.is_deleted == False)
        result = await self.db.execute(query)
        count = (await self.db.execute(count_q)).scalar() or 0
        return AgentRunList(
            items=[AgentRunResponse.model_validate(r) for r in result.scalars().all()],
            total=count,
        )

    async def get_agent_memory(
        self, agent_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[AgentMemoryResponse]:
        await self._get_agent_or_raise(agent_id, user_id)
        query = (
            select(AgentMemory)
            .where(AgentMemory.agent_id == agent_id, AgentMemory.is_deleted == False)
            .order_by(AgentMemory.created_at.desc())
        )
        result = await self.db.execute(query)
        return [AgentMemoryResponse.model_validate(m) for m in result.scalars().all()]

    async def add_agent_memory(
        self, agent_id: uuid.UUID, user_id: uuid.UUID, key: str, value: str, memory_type: str = "fact", relevance: float = 1.0
    ) -> AgentMemoryResponse:
        await self._get_agent_or_raise(agent_id, user_id)
        mem = AgentMemory(
            agent_id=agent_id,
            key=key,
            value=value,
            memory_type=memory_type,
            relevance_score=relevance,
        )
        self.db.add(mem)
        await self.db.flush()
        await self.db.refresh(mem)
        return AgentMemoryResponse.model_validate(mem)

    async def delete_agent_memory(self, agent_id: uuid.UUID, memory_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self._get_agent_or_raise(agent_id, user_id)
        mem = await self.db.get(AgentMemory, memory_id)
        if not mem or mem.agent_id != agent_id:
            raise NotFoundError(message="Memory entry not found")
        mem.is_deleted = True
        await self.db.flush()

    async def get_agent_tools(
        self, agent_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[AgentToolResponse]:
        await self._get_agent_or_raise(agent_id, user_id)
        query = select(AgentTool).where(AgentTool.agent_id == agent_id, AgentTool.is_deleted == False)
        result = await self.db.execute(query)
        return [AgentToolResponse.model_validate(t) for t in result.scalars().all()]

    async def set_agent_tool(
        self, agent_id: uuid.UUID, user_id: uuid.UUID, tool_name: str, enabled: bool = True, config: dict | None = None
    ) -> AgentToolResponse:
        await self._get_agent_or_raise(agent_id, user_id)
        query = select(AgentTool).where(AgentTool.agent_id == agent_id, AgentTool.tool_name == tool_name, AgentTool.is_deleted == False)
        existing = (await self.db.execute(query)).scalar_one_or_none()
        if existing:
            existing.enabled = enabled
            if config is not None:
                existing.config = config
            await self.db.flush()
            await self.db.refresh(existing)
            return AgentToolResponse.model_validate(existing)
        tool = AgentTool(agent_id=agent_id, tool_name=tool_name, enabled=enabled, config=config)
        self.db.add(tool)
        await self.db.flush()
        await self.db.refresh(tool)
        return AgentToolResponse.model_validate(tool)

    async def send_agent_message(
        self, agent_id: uuid.UUID, user_id: uuid.UUID, message: str, conversation_id: uuid.UUID | None = None
    ) -> dict:
        agent = await self._get_agent_or_raise(agent_id, user_id)
        if agent.status != "active":
            raise ValidationError(message="Agent is not active")

        conv_id = conversation_id
        if not conv_id:
            conv = Conversation(
                user_id=user_id,
                title=f"Chat with {agent.name}",
                agent_type=agent.name,
                model_used=agent.model,
                knowledge_base_id=agent.knowledge_base_id if agent.rag_enabled else None,
            )
            self.db.add(conv)
            await self.db.flush()
            conv_id = conv.id

        user_msg = Message(conversation_id=conv_id, role="user", content=message, agent_type=agent.name)
        self.db.add(user_msg)

        system_content = agent.system_prompt or DEFAULT_SYSTEM_PROMPTS.get("general", "You are a helpful AI assistant.")

        context = ""
        if agent.rag_enabled and agent.knowledge_base_id:
            kb = await self.db.get(KnowledgeBase, agent.knowledge_base_id)
            if kb:
                context = f"\n\nKnowledge Base context: {kb.description or ''}"

        memory_context = ""
        if agent.memory_enabled:
            mem_query = (
                select(AgentMemory)
                .where(AgentMemory.agent_id == agent_id, AgentMemory.is_deleted == False)
                .order_by(AgentMemory.created_at.desc())
                .limit(20)
            )
            mems = (await self.db.execute(mem_query)).scalars().all()
            if mems:
                memory_context = "\n\nRelevant memories:\n" + "\n".join(f"- {m.key}: {m.value}" for m in mems)

        full_system = system_content + context + memory_context
        conversation_history = ""
        hist_query = (
            select(Message)
            .where(Message.conversation_id == conv_id)
            .order_by(Message.created_at.asc())
            .limit(50)
        )
        hist_msgs = (await self.db.execute(hist_query)).scalars().all()
        for m in hist_msgs:
            conversation_history += f"{m.role}: {m.content}\n"

        from app.agents.base.agent import BaseAgent
        from app.core.config import settings

        class DynamicAgent(BaseAgent):
            agent_type = agent.name

            def _get_system_prompt(self, input_data: dict | None = None) -> str:
                return full_system

        dynamic_agent = DynamicAgent()
        dynamic_agent.model = agent.model
        dynamic_agent.temperature = agent.temperature
        dynamic_agent.max_tokens = agent.max_tokens

        started_at = datetime.now(timezone.utc)
        try:
            response_text = await dynamic_agent._generate_response(
                system_prompt=full_system,
                messages=[{"role": "user", "content": message}],
            )
            completed_at = datetime.now(timezone.utc)
            latency = int((completed_at - started_at).total_seconds() * 1000)

            total_tokens_est = len(message.split()) + len(response_text.split())
            prompt_tokens = len(message.split()) * 2
            completion_tokens = len(response_text.split()) * 2

            assistant_msg = Message(
                conversation_id=conv_id,
                role="assistant",
                content=response_text,
                model_used=agent.model,
                token_count=total_tokens_est,
            )
            self.db.add(assistant_msg)

            run = AgentRun(
                agent_id=agent_id,
                user_id=user_id,
                conversation_id=conv_id,
                input_text=message,
                output_text=response_text,
                tokens_prompt=prompt_tokens,
                tokens_completion=completion_tokens,
                tokens_total=total_tokens_est,
                latency_ms=latency,
                cost_usd=0.0,
                success=True,
                model_used=agent.model,
                provider_used=agent.provider,
                started_at=started_at,
                completed_at=completed_at,
            )
            self.db.add(run)

            conv_upd = await self.db.get(Conversation, conv_id)
            if conv_upd:
                conv_upd.message_count = (conv_upd.message_count or 0) + 2

            await self.db.flush()

            return {
                "conversation_id": conv_id,
                "message": response_text,
                "role": "assistant",
                "agent_name": agent.name,
                "tokens": total_tokens_est,
                "latency_ms": latency,
            }

        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            latency = int((completed_at - started_at).total_seconds() * 1000)
            error_text = str(e)

            run = AgentRun(
                agent_id=agent_id,
                user_id=user_id,
                conversation_id=conv_id,
                input_text=message,
                output_text=None,
                tokens_prompt=0,
                tokens_completion=0,
                tokens_total=0,
                latency_ms=latency,
                cost_usd=0.0,
                success=False,
                error=error_text,
                model_used=agent.model,
                provider_used=agent.provider,
                started_at=started_at,
                completed_at=completed_at,
            )
            self.db.add(run)
            await self.db.flush()

            raise

    async def _get_agent_or_raise(self, agent_id: uuid.UUID, user_id: uuid.UUID) -> Agent:
        agent = await self.repo.get_by_id(agent_id)
        if not agent or agent.is_deleted or agent.user_id != user_id:
            raise NotFoundError(message="Agent not found")
        return agent

    async def _get_agent_stats(self, agent_id: uuid.UUID, user_id: uuid.UUID) -> dict:
        base = AgentRun.agent_id == agent_id
        total_q = select(func.count()).select_from(AgentRun).where(base)
        success_q = select(func.count()).select_from(AgentRun).where(base, AgentRun.success == True)
        tokens_q = select(func.sum(AgentRun.tokens_total)).select_from(AgentRun).where(base)
        cost_q = select(func.sum(AgentRun.cost_usd)).select_from(AgentRun).where(base)
        avg_lat_q = select(func.avg(AgentRun.latency_ms)).select_from(AgentRun).where(base)
        last_q = select(AgentRun.started_at).where(base).order_by(AgentRun.started_at.desc()).limit(1)
        conv_q = select(func.count()).select_from(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.agent_type == select(Agent.name).where(Agent.id == agent_id).scalar_subquery(),
            Conversation.is_deleted == False,
        )

        total = (await self.db.execute(total_q)).scalar() or 0
        success_count = (await self.db.execute(success_q)).scalar() or 0
        total_tokens = (await self.db.execute(tokens_q)).scalar() or 0
        total_cost = (await self.db.execute(cost_q)).scalar() or 0.0
        avg_lat = (await self.db.execute(avg_lat_q)).scalar() or 0.0
        last_run = (await self.db.execute(last_q)).scalar()
        active_conv = (await self.db.execute(conv_q)).scalar() or 0

        return {
            "total_runs": total,
            "last_run_at": last_run,
            "avg_latency_ms": round(float(avg_lat), 2),
            "success_rate": round(success_count / total * 100, 1) if total > 0 else 0.0,
            "total_tokens": total_tokens,
            "total_cost": round(float(total_cost), 6),
            "active_conversations": active_conv,
        }

    async def get_agent_providers(self) -> list[dict]:
        return [
            {"value": "openrouter", "label": "OpenRouter", "default_model": "openai/gpt-oss-120b:free", "free": True},
            {"value": "openai", "label": "OpenAI", "default_model": "gpt-3.5-turbo", "free": False},
            {"value": "anthropic", "label": "Anthropic", "default_model": "claude-3-haiku", "free": False},
            {"value": "google", "label": "Google", "default_model": "gemini-1.5-flash", "free": True},
            {"value": "groq", "label": "Groq", "default_model": "mixtral-8x7b-32768", "free": True},
            {"value": "ollama", "label": "Ollama (Local)", "default_model": "llama3", "free": True},
        ]

    async def get_available_tools(self) -> list[dict]:
        return [
            {"value": "internet_search", "label": "Internet Search", "description": "Search the web for information"},
            {"value": "knowledge_base", "label": "Knowledge Base", "description": "Query your knowledge bases"},
            {"value": "code_interpreter", "label": "Code Interpreter", "description": "Run Python code"},
            {"value": "image_analysis", "label": "Image Analysis", "description": "Analyze uploaded images"},
            {"value": "document_search", "label": "Document Search", "description": "Search uploaded documents"},
            {"value": "web_scraping", "label": "Web Scraping", "description": "Extract content from websites"},
            {"value": "calculator", "label": "Calculator", "description": "Perform mathematical calculations"},
            {"value": "memory", "label": "Memory", "description": "Store and recall conversation context"},
            {"value": "workflow", "label": "Workflow Execution", "description": "Run automated workflows"},
            {"value": "file_upload", "label": "File Upload", "description": "Process uploaded files"},
            {"value": "vision", "label": "Vision", "description": "Process images with vision models"},
            {"value": "image_generation", "label": "Image Generation", "description": "Generate images from descriptions"},
        ]
