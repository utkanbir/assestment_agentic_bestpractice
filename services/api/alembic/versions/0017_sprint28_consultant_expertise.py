"""S28: consultant expertise JSONB + answer consultant_review_feedback

Revision ID: 0017
Revises: 0016
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE consultants
        ALTER COLUMN expertise TYPE JSONB
        USING CASE
            WHEN expertise IS NULL OR trim(expertise) = '' THEN '[]'::jsonb
            ELSE jsonb_build_array(expertise)
        END
        """
    )
    op.execute("ALTER TABLE consultants ALTER COLUMN expertise SET DEFAULT '[]'::jsonb")
    op.add_column(
        "answers",
        sa.Column("consultant_review_feedback", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("answers", "consultant_review_feedback")
    op.execute(
        """
        ALTER TABLE consultants
        ALTER COLUMN expertise TYPE TEXT
        USING CASE
            WHEN expertise IS NULL OR expertise = '[]'::jsonb THEN NULL
            ELSE expertise->>0
        END
        """
    )
    op.execute("ALTER TABLE consultants ALTER COLUMN expertise DROP DEFAULT")
