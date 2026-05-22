from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.domain.structure.types import ProposalStatus

if TYPE_CHECKING:
    from app.models.article_candidate import ArticleCandidate
    from app.models.project import Project


class StructureProposal(Base):
    __tablename__ = "structure_proposals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[ProposalStatus] = mapped_column(
        Enum(ProposalStatus),
        nullable=False,
        default=ProposalStatus.PENDING,
    )
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship("Project")
    candidates: Mapped[list["ArticleCandidate"]] = relationship(
        "ArticleCandidate",
        back_populates="proposal",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ArticleCandidate.suggested_order",
    )
