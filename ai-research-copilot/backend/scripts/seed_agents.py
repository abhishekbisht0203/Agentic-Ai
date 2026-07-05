"""
Seed script to populate default agent configurations.

Run with:
    python -m scripts.seed_agents
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.database.base import Base
from app.models.workflow import AgentConfiguration
from app.llms.prompts.templates import (
    RESEARCH_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    DATA_ANALYST_SYSTEM_PROMPT,
    CRITIC_SYSTEM_PROMPT,
    CODE_ASSISTANT_SYSTEM_PROMPT,
    AUTOMATION_SYSTEM_PROMPT,
    DOCUMENT_QA_SYSTEM_PROMPT,
    MEMORY_SYSTEM_PROMPT,
    GENERAL_SYSTEM_PROMPT,
)

DEFAULT_AGENTS = [
    {
        "name": "Research Agent",
        "agent_type": "research",
        "description": "Gathers, evaluates, and synthesises information on a given topic.",
        "system_prompt": RESEARCH_SYSTEM_PROMPT,
        "model": "openai/gpt-oss-120b:free",
        "temperature": 0.7,
        "max_tokens": 4096,
        "tools": None,
        "metadata_extra": None,
        "is_active": True,
    },
    {
        "name": "Planner Agent",
        "agent_type": "planner",
        "description": "Breaks complex tasks into step-by-step plans.",
        "system_prompt": PLANNER_SYSTEM_PROMPT,
        "model": "openai/gpt-oss-120b:free",
        "temperature": 0.5,
        "max_tokens": 4096,
        "tools": None,
        "metadata_extra": None,
        "is_active": True,
    },
    {
        "name": "Data Analyst Agent",
        "agent_type": "data_analyst",
        "description": "Analyses datasets, generates statistics, and suggests visualisations.",
        "system_prompt": DATA_ANALYST_SYSTEM_PROMPT,
        "model": "openai/gpt-oss-120b:free",
        "temperature": 0.3,
        "max_tokens": 4096,
        "tools": None,
        "metadata_extra": None,
        "is_active": True,
    },
    {
        "name": "Critic Agent",
        "agent_type": "critic",
        "description": "Evaluates content quality, identifies weaknesses, and provides feedback.",
        "system_prompt": CRITIC_SYSTEM_PROMPT,
        "model": "openai/gpt-oss-120b:free",
        "temperature": 0.5,
        "max_tokens": 4096,
        "tools": None,
        "metadata_extra": None,
        "is_active": True,
    },
    {
        "name": "Code Assistant Agent",
        "agent_type": "code_assistant",
        "description": "Writes, reviews, debugs, and explains code.",
        "system_prompt": CODE_ASSISTANT_SYSTEM_PROMPT,
        "model": "openai/gpt-oss-120b:free",
        "temperature": 0.3,
        "max_tokens": 4096,
        "tools": None,
        "metadata_extra": None,
        "is_active": True,
    },
    {
        "name": "Automation Agent",
        "agent_type": "automation",
        "description": "Designs and executes automated workflows.",
        "system_prompt": AUTOMATION_SYSTEM_PROMPT,
        "model": "openai/gpt-oss-120b:free",
        "temperature": 0.5,
        "max_tokens": 4096,
        "tools": None,
        "metadata_extra": None,
        "is_active": True,
    },
    {
        "name": "Document Q&A Agent",
        "agent_type": "document_qa",
        "description": "Answers questions about uploaded documents using RAG.",
        "system_prompt": DOCUMENT_QA_SYSTEM_PROMPT,
        "model": "openai/gpt-oss-120b:free",
        "temperature": 0.3,
        "max_tokens": 4096,
        "tools": None,
        "metadata_extra": None,
        "is_active": True,
    },
    {
        "name": "Memory Agent",
        "agent_type": "memory",
        "description": "Extracts and stores important facts from conversations.",
        "system_prompt": MEMORY_SYSTEM_PROMPT,
        "model": "openai/gpt-oss-120b:free",
        "temperature": 0.3,
        "max_tokens": 4096,
        "tools": None,
        "metadata_extra": None,
        "is_active": True,
    },
    {
        "name": "General Agent",
        "agent_type": "general",
        "description": "General-purpose chat that doesn't fit a specialist.",
        "system_prompt": GENERAL_SYSTEM_PROMPT,
        "model": "openai/gpt-oss-120b:free",
        "temperature": 0.7,
        "max_tokens": 4096,
        "tools": None,
        "metadata_extra": None,
        "is_active": True,
    },
]


async def seed_agent_configs():
    db_url = settings.database.async_database_url
    print(f"Connecting to database...")
    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables created/verified.")

    async with async_session() as session:
        created = 0
        skipped = 0
        for agent_data in DEFAULT_AGENTS:
            result = await session.execute(
                select(AgentConfiguration).where(
                    AgentConfiguration.agent_type == agent_data["agent_type"]
                )
            )
            if result.scalar_one_or_none():
                print(f"  Agent '{agent_data['agent_type']}' already exists, skipping.")
                skipped += 1
                continue

            config = AgentConfiguration(**agent_data)
            session.add(config)
            print(f"  Created agent: {agent_data['name']} ({agent_data['agent_type']})")
            created += 1

        await session.commit()
        print(f"\nSeed completed! Created: {created}, Skipped: {skipped}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_agent_configs())
