"""sprint17 recommendation roadmap fields and maturity target

Revision ID: 0012
Revises: 0011
"""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("recommendations", sa.Column("title", sa.String(500), nullable=True))
    op.add_column("recommendations", sa.Column("horizon", sa.String(20), nullable=True))
    op.add_column("recommendations", sa.Column("reviewer_note", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("reviewer_note", sa.Text(), nullable=True))
    op.add_column("risks", sa.Column("reviewer_note", sa.Text(), nullable=True))
    op.add_column(
        "maturity_scores",
        sa.Column("target_score", sa.Numeric(3, 1), nullable=True),
    )


def downgrade():
    op.drop_column("maturity_scores", "target_score")
    op.drop_column("risks", "reviewer_note")
    op.drop_column("findings", "reviewer_note")
    op.drop_column("recommendations", "reviewer_note")
    op.drop_column("recommendations", "horizon")
    op.drop_column("recommendations", "title")
