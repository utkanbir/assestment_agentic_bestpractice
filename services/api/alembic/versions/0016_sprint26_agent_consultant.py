"""S26: consultant_id on agent learning events

Revision ID: 0016
Revises: 0015
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agent_learning_events",
        sa.Column("consultant_id", sa.UUID(), sa.ForeignKey("consultants.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agent_learning_events", "consultant_id")
