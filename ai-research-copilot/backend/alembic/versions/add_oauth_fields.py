"""Add dedicated OAuth fields (google_id, github_id) to users table.

Revision ID: add_oauth_fields_001
Revises: None
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "add_oauth_fields_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add google_id and github_id columns to users table."""
    # Add google_id column with unique constraint
    op.add_column(
        "users",
        sa.Column(
            "google_id",
            sa.String(255),
            nullable=True,
            unique=True,
            comment="Google OAuth user ID",
        ),
    )

    # Add github_id column with unique constraint
    op.add_column(
        "users",
        sa.Column(
            "github_id",
            sa.String(255),
            nullable=True,
            unique=True,
            comment="GitHub OAuth user ID",
        ),
    )

    # Add indexes for faster lookups
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)
    op.create_index("ix_users_github_id", "users", ["github_id"], unique=True)


def downgrade() -> None:
    """Remove google_id and github_id columns from users table."""
    op.drop_index("ix_users_github_id", table_name="users")
    op.drop_index("ix_users_google_id", table_name="users")
    op.drop_column("users", "github_id")
    op.drop_column("users", "google_id")
