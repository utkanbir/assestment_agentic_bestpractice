"""sprint16 chat sessions and layer transactions

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "layer_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("assessment_id", UUID(as_uuid=True), nullable=True),
        sa.Column("interview_id", UUID(as_uuid=True), nullable=True),
        sa.Column("chat_session_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="completed"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_duration_ms", sa.Integer(), nullable=True),
    )
    op.create_index("ix_layer_transactions_operation", "layer_transactions", ["operation"])
    op.create_index("ix_layer_transactions_source", "layer_transactions", ["source"])
    op.create_index("ix_layer_transactions_assessment_id", "layer_transactions", ["assessment_id"])
    op.create_index("ix_layer_transactions_interview_id", "layer_transactions", ["interview_id"])
    op.create_index("ix_layer_transactions_chat_session_id", "layer_transactions", ["chat_session_id"])
    op.create_index("ix_layer_transactions_started_at", "layer_transactions", ["started_at"])

    op.add_column("layer_touch_events", sa.Column("transaction_id", UUID(as_uuid=True), nullable=True))
    op.add_column("layer_touch_events", sa.Column("step_order", sa.Integer(), nullable=True))
    op.create_index("ix_layer_touch_events_transaction_id", "layer_touch_events", ["transaction_id"])

    op.create_table(
        "chat_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("assessment_id", UUID(as_uuid=True), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workstream", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False, server_default="Yeni Sohbet"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_sessions_assessment_id", "chat_sessions", ["assessment_id"])
    op.create_index("ix_chat_sessions_workstream", "chat_sessions", ["workstream"])
    op.create_index("ix_chat_sessions_created_at", "chat_sessions", ["created_at"])

    op.create_table(
        "chat_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])
    op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"])


def downgrade():
    op.drop_index("ix_chat_messages_created_at", table_name="chat_messages")
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("ix_chat_sessions_created_at", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_workstream", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_assessment_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")

    op.drop_index("ix_layer_touch_events_transaction_id", table_name="layer_touch_events")
    op.drop_column("layer_touch_events", "step_order")
    op.drop_column("layer_touch_events", "transaction_id")

    op.drop_index("ix_layer_transactions_started_at", table_name="layer_transactions")
    op.drop_index("ix_layer_transactions_chat_session_id", table_name="layer_transactions")
    op.drop_index("ix_layer_transactions_interview_id", table_name="layer_transactions")
    op.drop_index("ix_layer_transactions_assessment_id", table_name="layer_transactions")
    op.drop_index("ix_layer_transactions_source", table_name="layer_transactions")
    op.drop_index("ix_layer_transactions_operation", table_name="layer_transactions")
    op.drop_table("layer_transactions")
