"""add evaluation column to answers

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-17
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("answers", sa.Column("evaluation", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("answers", "evaluation")
