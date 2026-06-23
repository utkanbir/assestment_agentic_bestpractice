"""S29: multi-consultant comments per answer

Revision ID: 0018
Revises: 0017
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "answer_consultant_comments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("answer_id", UUID(as_uuid=True), sa.ForeignKey("answers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("consultant_id", UUID(as_uuid=True), sa.ForeignKey("consultants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("consultant_review_feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("answer_id", "consultant_id", name="uq_answer_consultant_comment"),
    )
    op.create_index("ix_answer_consultant_comments_answer_id", "answer_consultant_comments", ["answer_id"])

    op.execute(
        """
        INSERT INTO answer_consultant_comments (id, answer_id, consultant_id, comment, consultant_review_feedback, created_at, updated_at)
        SELECT gen_random_uuid(), a.id, a.consultant_id, a.consultant_comment, a.consultant_review_feedback, a.created_at, a.updated_at
        FROM answers a
        WHERE a.consultant_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_answer_consultant_comments_answer_id", table_name="answer_consultant_comments")
    op.drop_table("answer_consultant_comments")
