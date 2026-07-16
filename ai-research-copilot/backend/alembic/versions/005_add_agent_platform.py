"""Add agent platform tables (agents, agent_runs, agent_memory, agent_tools).

Revision ID: 005_add_agent_platform
Revises: 004_add_llm_requests
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "005_add_agent_platform"
down_revision = "004_add_llm_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("avatar", sa.String(100), nullable=True),
        sa.Column("icon", sa.String(50), server_default="Bot"),
        sa.Column("color", sa.String(7), server_default="#6366f1"),
        sa.Column("model", sa.String(100), server_default="openai/gpt-oss-120b:free"),
        sa.Column("provider", sa.String(50), server_default="openrouter"),
        sa.Column("temperature", sa.Float(), server_default="0.7"),
        sa.Column("max_tokens", sa.Integer(), server_default="4096"),
        sa.Column("top_p", sa.Float(), server_default="1.0"),
        sa.Column("frequency_penalty", sa.Float(), server_default="0.0"),
        sa.Column("presence_penalty", sa.Float(), server_default="0.0"),
        sa.Column("tools_enabled", JSONB(), nullable=True),
        sa.Column("knowledge_base_id", UUID(as_uuid=True), sa.ForeignKey("knowledge_bases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("memory_enabled", sa.Boolean(), server_default="false"),
        sa.Column("rag_enabled", sa.Boolean(), server_default="false"),
        sa.Column("workflow_enabled", sa.Boolean(), server_default="false"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("visibility", sa.String(20), server_default="private"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_agents_user_id", "agents", ["user_id"])
    op.create_index("ix_agents_provider", "agents", ["provider"])
    op.create_index("ix_agents_status", "agents", ["status"])

    op.create_table(
        "agent_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column("tokens_prompt", sa.Integer(), server_default="0"),
        sa.Column("tokens_completion", sa.Integer(), server_default="0"),
        sa.Column("tokens_total", sa.Integer(), server_default="0"),
        sa.Column("latency_ms", sa.Integer(), server_default="0"),
        sa.Column("cost_usd", sa.Float(), server_default="0.0"),
        sa.Column("success", sa.Boolean(), server_default="true"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("provider_used", sa.String(50), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_agent_runs_agent_id", "agent_runs", ["agent_id"])
    op.create_index("ix_agent_runs_user_id", "agent_runs", ["user_id"])
    op.create_index("ix_agent_runs_created_at", "agent_runs", ["created_at"])

    op.create_table(
        "agent_memory",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("memory_type", sa.String(50), server_default="fact"),
        sa.Column("relevance_score", sa.Float(), server_default="1.0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_agent_memory_agent_id", "agent_memory", ["agent_id"])

    op.create_table(
        "agent_tools",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
        sa.Column("config", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_agent_tools_agent_id", "agent_tools", ["agent_id"])


def downgrade() -> None:
    op.drop_table("agent_tools")
    op.drop_table("agent_memory")
    op.drop_table("agent_runs")
    op.drop_table("agents")
