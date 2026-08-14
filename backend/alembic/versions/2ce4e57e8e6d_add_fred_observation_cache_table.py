"""add fred observation cache table

Revision ID: 2ce4e57e8e6d
Revises:
Create Date: 2026-08-11 19:58:45.802806

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2ce4e57e8e6d"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fred_observation_cache",
        sa.Column("series_id", sa.String(length=64), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("series_id", "observation_date"),
    )


def downgrade() -> None:
    op.drop_table("fred_observation_cache")
