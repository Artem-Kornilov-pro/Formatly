"""backfill gost profile with new formatting rules

Revision ID: 8a33bfcbf7ff
Revises: 3567f8ead3fa
Create Date: 2026-07-26 07:29:37.936459

"""
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8a33bfcbf7ff'
down_revision: str | Sequence[str] | None = '3567f8ead3fa'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

GOST_PROFILE_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

NEW_FIELDS = {
    "bold_headings": True,
    "italic_headings": False,
    "center_headings": True,
    "heading_size_bump_pt": 2,
    "page_break_before_heading_1": False,
    "paragraph_alignment": "justify",
    "paragraph_indent_enabled": True,
    "paragraph_indent_mm": 12.5,
}


def upgrade() -> None:
    op.execute(
        sa.text("UPDATE formatting_profiles SET rules = rules || :new_fields WHERE id = :id")
        .bindparams(
            sa.bindparam("new_fields", value=NEW_FIELDS, type_=postgresql.JSONB),
            sa.bindparam("id", value=GOST_PROFILE_ID, type_=postgresql.UUID),
        )
    )


def downgrade() -> None:
    keys = " - ".join(f"'{key}'" for key in NEW_FIELDS)
    op.execute(
        sa.text(f"UPDATE formatting_profiles SET rules = rules - {keys} WHERE id = :id")
        .bindparams(sa.bindparam("id", value=GOST_PROFILE_ID, type_=postgresql.UUID))
    )
