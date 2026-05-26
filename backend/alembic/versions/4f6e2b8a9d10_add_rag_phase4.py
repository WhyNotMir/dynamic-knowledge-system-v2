"""add rag phase4

Revision ID: 4f6e2b8a9d10
Revises: 8a1b7d4f2c31
Create Date: 2026-05-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "4f6e2b8a9d10"
down_revision: Union[str, Sequence[str], None] = "8a1b7d4f2c31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class Vector(sa.types.UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw) -> str:
        return "vector"


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("DROP TABLE IF EXISTS article_block_embeddings")

    op.add_column("projects", sa.Column("settings", postgresql.JSONB(), nullable=True))
    op.add_column("source_fragments", sa.Column("embedding", Vector(), nullable=True))
    op.add_column("source_fragments", sa.Column("embedding_model", sa.String(length=255), nullable=True))
    op.add_column("source_fragments", sa.Column("embedding_dimension", sa.Integer(), nullable=True))
    op.add_column(
        "source_fragments",
        sa.Column("embedding_content_hash", sa.String(length=64), nullable=True),
    )
    op.create_index(
        op.f("ix_source_fragments_embedding_model"),
        "source_fragments",
        ["embedding_model"],
    )
    op.create_index(
        op.f("ix_source_fragments_embedding_content_hash"),
        "source_fragments",
        ["embedding_content_hash"],
    )

    message_role = postgresql.ENUM("USER", "ASSISTANT", "SYSTEM", name="messagerole")
    citation_status = postgresql.ENUM("UNVALIDATED", name="citationstatus")
    message_role.create(op.get_bind(), checkfirst=True)
    citation_status.create(op.get_bind(), checkfirst=True)
    message_role_column = postgresql.ENUM(
        "USER",
        "ASSISTANT",
        "SYSTEM",
        name="messagerole",
        create_type=False,
    )
    citation_status_column = postgresql.ENUM(
        "UNVALIDATED",
        name="citationstatus",
        create_type=False,
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=96), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversations_project_id"), "conversations", ["project_id"])
    op.create_index(op.f("ix_conversations_user_id"), "conversations", ["user_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", message_role_column, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("position_index", sa.Integer(), nullable=False),
        sa.Column("meta_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conversation_id",
            "position_index",
            name="uq_messages_conversation_position",
        ),
    )
    op.create_index(op.f("ix_messages_conversation_id"), "messages", ["conversation_id"])

    op.create_table(
        "block_citations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("block_id", sa.Uuid(), nullable=False),
        sa.Column("fragment_id", sa.Uuid(), nullable=False),
        sa.Column("status", citation_status_column, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("verifier_version", sa.String(length=64), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["block_id"], ["article_blocks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fragment_id"], ["source_fragments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_block_citations_block_id"), "block_citations", ["block_id"])
    op.create_index(op.f("ix_block_citations_fragment_id"), "block_citations", ["fragment_id"])
    op.create_index(op.f("ix_block_citations_message_id"), "block_citations", ["message_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_block_citations_message_id"), table_name="block_citations")
    op.drop_index(op.f("ix_block_citations_fragment_id"), table_name="block_citations")
    op.drop_index(op.f("ix_block_citations_block_id"), table_name="block_citations")
    op.drop_table("block_citations")
    op.drop_index(op.f("ix_messages_conversation_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_index(op.f("ix_conversations_user_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_project_id"), table_name="conversations")
    op.drop_table("conversations")

    sa.Enum(name="citationstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="messagerole").drop(op.get_bind(), checkfirst=True)

    op.drop_index(op.f("ix_source_fragments_embedding_content_hash"), table_name="source_fragments")
    op.drop_index(op.f("ix_source_fragments_embedding_model"), table_name="source_fragments")
    op.drop_column("source_fragments", "embedding_content_hash")
    op.drop_column("source_fragments", "embedding_dimension")
    op.drop_column("source_fragments", "embedding_model")
    op.drop_column("source_fragments", "embedding")
    op.drop_column("projects", "settings")
