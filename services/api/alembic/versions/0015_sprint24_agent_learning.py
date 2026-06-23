"""sprint24 agent_learning_events for AAHA/text training

Revision ID: 0015
Revises: 0014
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_learning_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workstream", sa.String(100), nullable=False, index=True),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=True),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("source_doc_id", UUID(as_uuid=True), sa.ForeignKey("knowledge_documents.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("agent_learning_events")
