"""add knowledge_documents table for RAG pipeline

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "knowledge_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workstream", sa.String(100), nullable=False, index=True),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False, server_default="txt"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("knowledge_documents")
