"""add recipe notes

Revision ID: a8d3c5e9f210
Revises: f4a6c2d9b810
Create Date: 2026-05-21

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8d3c5e9f210"
down_revision: Union[str, Sequence[str], None] = "f4a6c2d9b810"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("recipes", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("recipes", "notes")
