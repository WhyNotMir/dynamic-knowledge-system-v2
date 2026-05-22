from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.domain.source import SourceStatus

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.source_fragment import SourceFragment


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)

    status: Mapped[SourceStatus] = mapped_column(
        Enum(SourceStatus),
        default=SourceStatus.PENDING,
        nullable=False,
    )

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="sources",
    )

    fragments: Mapped[list["SourceFragment"]] = relationship(
        "SourceFragment",
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SourceFragment.position_index",
    )
