from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.domain.rag.types import CitationStatus

if TYPE_CHECKING:
    from app.models.article import ArticleBlock
    from app.models.conversation import Message
    from app.models.source_fragment import SourceFragment


class BlockCitation(Base):
    __tablename__ = "block_citations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    block_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("article_blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fragment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_fragments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[CitationStatus] = mapped_column(
        Enum(CitationStatus),
        nullable=False,
        default=CitationStatus.UNVALIDATED,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    verifier_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    message: Mapped["Message"] = relationship("Message")
    block: Mapped["ArticleBlock"] = relationship("ArticleBlock")
    fragment: Mapped["SourceFragment"] = relationship("SourceFragment")
