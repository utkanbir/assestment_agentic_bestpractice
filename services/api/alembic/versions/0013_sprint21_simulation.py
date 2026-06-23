"""sprint21 simulated assessment fields

Revision ID: 0013
Revises: 0012
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "assessments",
        sa.Column("assessment_mode", sa.String(20), nullable=False, server_default="live"),
    )
    op.add_column(
        "assessments",
        sa.Column("simulation_status", sa.String(30), nullable=True),
    )
    op.add_column(
        "assessments",
        sa.Column("simulation_progress", JSONB, nullable=True),
    )
    op.add_column(
        "assessments",
        sa.Column("company_profile", JSONB, nullable=True),
    )


def downgrade():
    op.drop_column("assessments", "company_profile")
    op.drop_column("assessments", "simulation_progress")
    op.drop_column("assessments", "simulation_status")
    op.drop_column("assessments", "assessment_mode")
