from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass

from app.domain.ingestion.types import ElementType


class ProposalStatus(str, enum.Enum):
    PENDING = "pending"
    READY = "ready"
    REVIEWED = "reviewed"


class CandidateStatus(str, enum.Enum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


@dataclass(slots=True)
class FragmentForDetection:
    id: uuid.UUID
    source_id: uuid.UUID
    content: str
    element_type: ElementType
    position_index: int
    heading_level: int | None = None
    section_path: str | None = None


@dataclass(slots=True)
class DetectedCandidate:
    title: str
    source_section_path: str
    suggested_order: int
    fragment_ids: list[uuid.UUID]
