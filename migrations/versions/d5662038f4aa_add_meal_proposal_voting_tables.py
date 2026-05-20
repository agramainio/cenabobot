"""add meal proposal voting tables

Revision ID: d5662038f4aa
Revises: 1f838184763f
Create Date: 2026-05-20 20:44:20.526103

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5662038f4aa'
down_revision: Union[str, Sequence[str], None] = '1f838184763f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
