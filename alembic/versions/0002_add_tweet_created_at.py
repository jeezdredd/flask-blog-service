"""add tweet created_at timestamp

Revision ID: 0002_add_tweet_created_at
Revises: 0001_init
Create Date: 2025-03-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_tweet_created_at"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tweets",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("tweets", "created_at")
