"""Add llm_requests table for per-request token/cost tracking.

Revision ID: 004_add_llm_requests
Revises: 003_full_initial_schema
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "004_add_llm_requests"
down_revision = "003_full_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agent_type", sa.String(100), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(200), nullable=False),
        sa.Column("request_type", sa.String(50), server_default="chat"),
        sa.Column("prompt_tokens", sa.Integer(), server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), server_default="0"),
        sa.Column("total_tokens", sa.Integer(), server_default="0"),
        sa.Column("cost_usd", sa.Float(precision=10), server_default="0.0"),
        sa.Column("duration_ms", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(20), server_default="success"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("cached", sa.Integer(), server_default="0"),
        sa.Column("streaming", sa.Integer(), server_default="0"),
        sa.Column("metadata", JSONB(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_llm_requests_user_id", "llm_requests", ["user_id"])
    op.create_index("ix_llm_requests_conversation_id", "llm_requests", ["conversation_id"])
    op.create_index("ix_llm_requests_provider", "llm_requests", ["provider"])
    op.create_index("ix_llm_requests_model", "llm_requests", ["model"])
    op.create_index("ix_llm_requests_status", "llm_requests", ["status"])
    op.create_index("ix_llm_requests_requested_at", "llm_requests", ["requested_at"])
    op.create_index("ix_llm_requests_agent_type", "llm_requests", ["agent_type"])


def downgrade() -> None:
    op.drop_table("llm_requests")
