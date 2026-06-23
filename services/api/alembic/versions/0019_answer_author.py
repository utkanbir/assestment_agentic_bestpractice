"""S30: agent learning answer_author + approved_by_consultant_id

Revision ID: 0019
Revises: 0018
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0019"
down_revision: Union[str, None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agent_learning_events",
        sa.Column("answer_author", sa.String(20), nullable=False, server_default="consultant"),
    )
    op.add_column(
        "agent_learning_events",
        sa.Column("approved_by_consultant_id", UUID(as_uuid=True), sa.ForeignKey("consultants.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agent_learning_events", "approved_by_consultant_id")
    op.drop_column("agent_learning_events", "answer_author")
