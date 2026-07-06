"""Add conversation_id to documents table.

Revision ID: 002
Revises: add_oauth_fields
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = "002_add_conversation_id"
down_revision = "add_oauth_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add conversation_id column to documents table."""
    # Add the conversation_id column
    op.add_column(
        "documents",
        sa.Column(
            "conversation_id",
            UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    # Create index for efficient queries
    op.create_index(
        "ix_documents_conversation_id",
        "documents",
        ["conversation_id"],
    )


def downgrade() -> None:
    """Remove conversation_id column from documents table."""
    op.drop_index("ix_documents_conversation_id", table_name="documents")
    op.drop_column("documents", "conversation_id")
