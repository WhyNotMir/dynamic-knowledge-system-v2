from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.domain.structure.types import CandidateStatus

if TYPE_CHECKING:
    from app.models.source_fragment import SourceFragment
    from app.models.structure_proposal import StructureProposal


class ArticleCandidate(Base):
    __tablename__ = "article_candidates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    proposal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("structure_proposals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_section_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus),
        nullable=False,
        default=CandidateStatus.PROPOSED,
    )
    suggested_order: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    proposal: Mapped["StructureProposal"] = relationship(
        "StructureProposal",
        back_populates="candidates",
    )
    fragment_links: Mapped[list["ArticleCandidateFragment"]] = relationship(
        "ArticleCandidateFragment",
        back_populates="candidate",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ArticleCandidateFragment.position_index",
    )


class ArticleCandidateFragment(Base):
    __tablename__ = "article_candidate_fragments"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("article_candidates.id", ondelete="CASCADE"),
        primary_key=True,
    )
    fragment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_fragments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    position_index: Mapped[int] = mapped_column(Integer, nullable=False)

    candidate: Mapped["ArticleCandidate"] = relationship(
        "ArticleCandidate",
        back_populates="fragment_links",
    )
    fragment: Mapped["SourceFragment"] = relationship("SourceFragment")

    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "position_index",
            name="uq_article_candidate_fragments_candidate_position",
        ),
    )
