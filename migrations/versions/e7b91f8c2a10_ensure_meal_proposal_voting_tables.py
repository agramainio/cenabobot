"""ensure meal proposal voting tables exist

Revision ID: e7b91f8c2a10
Revises: d5662038f4aa
Create Date: 2026-05-20

This migration fixes the previous empty migration
d5662038f4aa_add_meal_proposal_voting_tables.py.

Production was hotfixed manually, so these CREATE TABLE IF NOT EXISTS
statements are intentionally idempotent.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "e7b91f8c2a10"
down_revision: Union[str, Sequence[str], None] = "d5662038f4aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS meal_proposals (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT NOT NULL REFERENCES telegram_groups(chat_id) ON DELETE CASCADE,
            message_id BIGINT,
            recipe_id VARCHAR(120) NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
            filter_key VARCHAR(120),
            status VARCHAR(40) NOT NULL DEFAULT 'open',
            created_by_user_id BIGINT REFERENCES telegram_users(user_id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ DEFAULT now(),
            accepted_at TIMESTAMPTZ
        );
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_meal_proposals_chat_status
        ON meal_proposals (chat_id, status);
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS meal_votes (
            id SERIAL PRIMARY KEY,
            proposal_id INTEGER NOT NULL REFERENCES meal_proposals(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL REFERENCES telegram_users(user_id) ON DELETE CASCADE,
            user_name VARCHAR(160),
            vote VARCHAR(40) NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT now(),
            CONSTRAINT uq_meal_vote_proposal_user UNIQUE (proposal_id, user_id)
        );
        """
    )


def downgrade() -> None:
    # Intentionally no-op.
    #
    # This is a corrective/idempotent migration for production safety.
    # Dropping these tables on downgrade could delete meal vote history.
    pass
