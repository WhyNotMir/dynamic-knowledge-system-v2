"""extend element type

Revision ID: 8a1b7d4f2c31
Revises: 9b1f7c6a2d44
Create Date: 2026-05-25 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "8a1b7d4f2c31"
down_revision: Union[str, Sequence[str], None] = "9b1f7c6a2d44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE elementtype ADD VALUE IF NOT EXISTS 'QUOTE'")
    op.execute("ALTER TYPE elementtype ADD VALUE IF NOT EXISTS 'CODE_BLOCK'")
    op.execute("ALTER TYPE elementtype ADD VALUE IF NOT EXISTS 'FOOTNOTE'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
