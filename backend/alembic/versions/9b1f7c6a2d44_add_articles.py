"""add articles

Revision ID: 9b1f7c6a2d44
Revises: c448a66d5401
Create Date: 2026-05-22 16:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9b1f7c6a2d44"
down_revision: Union[str, Sequence[str], None] = "c448a66d5401"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "articles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", name="articlestatus"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["article_candidates.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id"),
    )
    op.create_index(op.f("ix_articles_project_id"), "articles", ["project_id"])

    op.create_table(
        "article_blocks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("article_id", sa.Uuid(), nullable=False),
        sa.Column("fragment_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "element_type",
            postgresql.ENUM(
                "HEADING",
                "PARAGRAPH",
                "LIST_ITEM",
                "TABLE",
                "CAPTION",
                "IMAGE",
                "FORMULA",
                "REFERENCE",
                name="elementtype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("position_index", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("heading_level", sa.Integer(), nullable=True),
        sa.Column("section_path", sa.String(length=2048), nullable=True),
        sa.Column("meta_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["fragment_id"],
            ["source_fragments.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "article_id",
            "position_index",
            name="uq_article_blocks_article_position",
        ),
    )
    op.create_index(op.f("ix_article_blocks_article_id"), "article_blocks", ["article_id"])
    op.create_index(
        op.f("ix_article_blocks_fragment_id"),
        "article_blocks",
        ["fragment_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_article_blocks_fragment_id"), table_name="article_blocks")
    op.drop_index(op.f("ix_article_blocks_article_id"), table_name="article_blocks")
    op.drop_table("article_blocks")
    op.drop_index(op.f("ix_articles_project_id"), table_name="articles")
    op.drop_table("articles")
    sa.Enum(name="articlestatus").drop(op.get_bind(), checkfirst=True)
