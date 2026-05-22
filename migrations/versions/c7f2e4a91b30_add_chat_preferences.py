"""add chat preferences

Revision ID: c7f2e4a91b30
Revises: a8d3c5e9f210
Create Date: 2026-05-22

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7f2e4a91b30"
down_revision: Union[str, Sequence[str], None] = "a8d3c5e9f210"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_preferences",
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="fr"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["chat_id"], ["telegram_groups.chat_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chat_id"),
    )


def downgrade() -> None:
    op.drop_table("chat_preferences")
