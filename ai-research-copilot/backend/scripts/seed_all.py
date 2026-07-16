"""
Comprehensive seed script: creates a demo user, sample documents,
knowledge bases, conversations, agents, and workflows.

Run with:     python -m scripts.seed_all
Or with uv:   uv run python -m scripts.seed_all
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.security.auth import hash_password
from app.database.base import Base
from app.models.user import User, UserRole
from app.models.document import Document, KnowledgeBase, KnowledgeBaseDocument, DocumentChunk
from app.models.conversation import Conversation, Message
from app.models.workflow import AgentConfiguration, Workflow, WorkflowStatus, WorkflowType


DEMO_USER = {
    "email": "demo@airesearchcopilot.com",
    "username": "demo_user",
    "password": "Demo1234",
    "full_name": "Demo User",
    "role": UserRole.USER,
}

SAMPLE_WORKFLOWS = [
    {
        "name": "Literature Review Pipeline",
        "description": "Automatically reviews uploaded papers, extracts key findings, and generates a structured summary.",
        "workflow_type": WorkflowType.SEQUENTIAL,
        "status": WorkflowStatus.ACTIVE,
        "steps": [
            {"type": "agent_call", "config": {"agent_type": "research", "prompt": "Extract key findings"}},
            {"type": "agent_call", "config": {"agent_type": "critic", "prompt": "Review the summary for completeness"}},
            {"type": "tool_call", "config": {"tool": "generate_report", "format": "markdown"}},
        ],
    },
    {
        "name": "Competitive Analysis",
        "description": "Analyzes competitor documents and generates a structured competitive landscape report.",
        "workflow_type": WorkflowType.SEQUENTIAL,
        "status": WorkflowStatus.ACTIVE,
        "steps": [
            {"type": "agent_call", "config": {"agent_type": "data_analyst", "prompt": "Analyze competitive data"}},
            {"type": "agent_call", "config": {"agent_type": "research", "prompt": "Gather market intelligence"}},
        ],
    },
]


async def seed_database():
    db_url = settings.database.async_database_url
    print(f"Connecting to {db_url}...")
    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables verified.")

    async with async_session() as session:
        # ── Demo User ──────────────────────────────────────────────────────
        result = await session.execute(
            select(User).where(User.email == DEMO_USER["email"])
        )
        demo_user: User | None = result.scalar_one_or_none()
        if not demo_user:
            demo_user = User(
                email=DEMO_USER["email"],
                username=DEMO_USER["username"],
                hashed_password=hash_password(DEMO_USER["password"]),
                full_name=DEMO_USER["full_name"],
                role=DEMO_USER["role"],
                is_active=True,
                is_verified=True,
            )
            session.add(demo_user)
            await session.flush()
            print(f"Created demo user: {demo_user.email} / {DEMO_USER['password']}")
        else:
            print(f"Demo user already exists: {demo_user.email}")

        user_id = demo_user.id

        # ── Sample Knowledge Base ──────────────────────────────────────────
        kb_result = await session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.name == "AI Research Papers",
            )
        )
        kb = kb_result.scalar_one_or_none()
        if not kb:
            kb = KnowledgeBase(
                user_id=user_id,
                name="AI Research Papers",
                description="Collection of AI and machine learning research papers for analysis.",
            )
            session.add(kb)
            await session.flush()
            print(f"Created knowledge base: {kb.name}")
        else:
            print(f"Knowledge base already exists: {kb.name}")

        # ── Sample Documents ───────────────────────────────────────────────
        sample_docs = [
            {
                "name": "Attention Is All You Need.pdf",
                "original_filename": "Attention_Is_All_You_Need.pdf",
                "mime_type": "application/pdf",
                "file_size": 1048576,
                "status": "processed",
            },
            {
                "name": "BERT Pre-training of Deep Bidirectional Transformers.pdf",
                "original_filename": "BERT_Pre_training.pdf",
                "mime_type": "application/pdf",
                "file_size": 2097152,
                "status": "processed",
            },
            {
                "name": "RAG vs Fine-tuning Analysis.docx",
                "original_filename": "RAG_vs_Fine_tuning.docx",
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "file_size": 524288,
                "status": "processed",
            },
        ]
        doc_ids = []
        for doc_data in sample_docs:
            existing = await session.execute(
                select(Document).where(
                    Document.user_id == user_id,
                    Document.name == doc_data["name"],
                )
            )
            doc = existing.scalar_one_or_none()
            if not doc:
                doc = Document(user_id=user_id, **doc_data)
                session.add(doc)
                await session.flush()
                doc_ids.append(doc.id)
                print(f"  Created document: {doc.name}")
            else:
                doc_ids.append(doc.id)
                print(f"  Document already exists: {doc.name}")

            # Link to KB
            if doc_ids:
                link_exists = await session.execute(
                    select(KnowledgeBaseDocument).where(
                        KnowledgeBaseDocument.knowledge_base_id == kb.id,
                        KnowledgeBaseDocument.document_id == doc.id,
                    )
                )
                if not link_exists.scalar_one_or_none():
                    session.add(KnowledgeBaseDocument(
                        knowledge_base_id=kb.id,
                        document_id=doc.id,
                    ))

        # ── Agent Configurations (from seed_agents) ────────────────────────
        from app.llms.prompts.templates import (
            RESEARCH_SYSTEM_PROMPT, PLANNER_SYSTEM_PROMPT,
            DATA_ANALYST_SYSTEM_PROMPT, CRITIC_SYSTEM_PROMPT,
            CODE_ASSISTANT_SYSTEM_PROMPT, AUTOMATION_SYSTEM_PROMPT,
            DOCUMENT_QA_SYSTEM_PROMPT, MEMORY_SYSTEM_PROMPT, GENERAL_SYSTEM_PROMPT,
        )
        agents = [
            ("Research Agent", "research", RESEARCH_SYSTEM_PROMPT, 0.7),
            ("Planner Agent", "planner", PLANNER_SYSTEM_PROMPT, 0.5),
            ("Data Analyst Agent", "data_analyst", DATA_ANALYST_SYSTEM_PROMPT, 0.3),
            ("Critic Agent", "critic", CRITIC_SYSTEM_PROMPT, 0.5),
            ("Code Assistant Agent", "code_assistant", CODE_ASSISTANT_SYSTEM_PROMPT, 0.3),
            ("Automation Agent", "automation", AUTOMATION_SYSTEM_PROMPT, 0.5),
            ("Document Q&A Agent", "document_qa", DOCUMENT_QA_SYSTEM_PROMPT, 0.3),
            ("Memory Agent", "memory", MEMORY_SYSTEM_PROMPT, 0.3),
            ("General Agent", "general", GENERAL_SYSTEM_PROMPT, 0.7),
        ]
        for name, agent_type, prompt, temp in agents:
            existing = await session.execute(
                select(AgentConfiguration).where(
                    AgentConfiguration.agent_type == agent_type
                )
            )
            if not existing.scalar_one_or_none():
                config = AgentConfiguration(
                    name=name,
                    agent_type=agent_type,
                    description=f"{name} for automated research tasks.",
                    system_prompt=prompt,
                    model="openai/gpt-4o-mini",
                    temperature=temp,
                    max_tokens=4096,
                    is_active=True,
                )
                session.add(config)
                print(f"  Created agent config: {name}")

        # ── Sample Conversation ────────────────────────────────────────────
        conv_result = await session.execute(
            select(Conversation).where(
                Conversation.user_id == user_id,
                Conversation.title == "Getting Started with ARC",
            )
        )
        conv = conv_result.scalar_one_or_none()
        if not conv:
            conv = Conversation(
                user_id=user_id,
                title="Getting Started with ARC",
                knowledge_base_id=kb.id,
            )
            session.add(conv)
            await session.flush()

            messages = [
                ("user", "What is ARC and how does it work?"),
                ("assistant", "ARC (AI Research Copilot) is an intelligent research platform that helps you analyze documents, build knowledge bases, chat with AI about your content, and automate research workflows. It uses Retrieval-Augmented Generation (RAG) to provide accurate, cited answers based on your uploaded documents."),
                ("user", "What file formats do you support?"),
                ("assistant", "ARC supports PDF, DOCX, TXT, and Markdown files. When you upload a document, it goes through several processing steps:\n\n1. **Text Extraction** - Content is extracted from the file\n2. **Intelligent Chunking** - Text is split into meaningful segments\n3. **Embedding Generation** - Each chunk is converted to a vector embedding\n4. **Indexing** - Vectors are stored in Qdrant for fast semantic search\n\nThis process typically takes just a few seconds."),
                ("user", "Can you summarize the key benefits of using ARC?"),
                ("assistant", "Here are the key benefits of using ARC:\n\n**1. Speed** - Find answers across thousands of documents in seconds\n**2. Accuracy** - RAG ensures responses are grounded in your actual documents, with source citations\n**3. Automation** - AI agents and workflows handle repetitive research tasks\n**4. Multi-Model** - Supports GPT-4o, Claude 3.5 Sonnet, and Gemini\n**5. Collaboration** - Share knowledge bases with your team\n\nResearchers typically report **60%+ time savings** on literature review and analysis tasks."),
            ]
            for role, content in messages:
                msg = Message(
                    conversation_id=conv.id,
                    user_id=user_id,
                    role=role,
                    content=content,
                )
                session.add(msg)
            print(f"Created sample conversation with {len(messages)} messages")
        else:
            print(f"Sample conversation already exists")

        # ── Sample Workflows ───────────────────────────────────────────────
        for wf_data in SAMPLE_WORKFLOWS:
            existing = await session.execute(
                select(Workflow).where(
                    Workflow.user_id == user_id,
                    Workflow.name == wf_data["name"],
                )
            )
            if not existing.scalar_one_or_none():
                wf = Workflow(
                    user_id=user_id,
                    name=wf_data["name"],
                    description=wf_data["description"],
                    workflow_type=wf_data["workflow_type"],
                    status=wf_data["status"],
                    steps=wf_data["steps"],
                )
                session.add(wf)
                print(f"Created workflow: {wf.name}")

        await session.commit()
        print(f"\n✓ Seed completed successfully!")
        print(f"  Demo user: {DEMO_USER['email']} / {DEMO_USER['password']}")
        print(f"  Login at: http://localhost:3000/login")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
