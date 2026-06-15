"""add title and kg_uri to risks

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("risks", sa.Column("title", sa.String(500), nullable=True))
    op.add_column("risks", sa.Column("kg_uri", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("risks", "kg_uri")
    op.drop_column("risks", "title")
