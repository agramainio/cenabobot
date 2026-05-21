"""add recipe import drafts

Revision ID: f4a6c2d9b810
Revises: e7b91f8c2a10
Create Date: 2026-05-21

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4a6c2d9b810"
down_revision: Union[str, Sequence[str], None] = "e7b91f8c2a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recipe_import_drafts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("submitted_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("submitted_by_name", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("proposed_recipe_id", sa.String(length=120), nullable=True),
        sa.Column("proposed_title", sa.String(length=240), nullable=True),
        sa.Column("proposed_yaml", sa.Text(), nullable=True),
        sa.Column("warnings", sa.Text(), nullable=True),
        sa.Column("validation_errors", sa.Text(), nullable=True),
        sa.Column("approved_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["telegram_users.user_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["telegram_users.user_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_recipe_import_drafts_status_created",
        "recipe_import_drafts",
        ["status", "created_at"],
    )

    op.create_index(
        "ix_recipe_import_drafts_submitted_by",
        "recipe_import_drafts",
        ["submitted_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_recipe_import_drafts_submitted_by", table_name="recipe_import_drafts")
    op.drop_index("ix_recipe_import_drafts_status_created", table_name="recipe_import_drafts")
    op.drop_table("recipe_import_drafts")
