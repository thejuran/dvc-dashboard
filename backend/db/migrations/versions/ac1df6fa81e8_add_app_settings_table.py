"""add_app_settings_table

Revision ID: ac1df6fa81e8
Revises: a19dc6af5d1e
Create Date: 2026-02-10 18:03:44.805889

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ac1df6fa81e8'
down_revision: str | None = 'a19dc6af5d1e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('app_settings',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )
    # Seed default borrowing policy
    op.execute("INSERT INTO app_settings (key, value) VALUES ('borrowing_limit_pct', '100')")


def downgrade() -> None:
    op.drop_table('app_settings')
