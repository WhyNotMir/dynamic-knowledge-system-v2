import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.domain.structure.types import CandidateStatus, ProposalStatus


class UpdateCandidateRequest(BaseModel):
    title: str | None = None
    status: CandidateStatus | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Title must not be blank")
        return stripped


class ConfirmAllResponse(BaseModel):
    updated_count: int


class ArticleCandidateFragmentResponse(BaseModel):
    fragment_id: uuid.UUID
    position_index: int
    content: str


class ArticleCandidateResponse(BaseModel):
    id: uuid.UUID
    proposal_id: uuid.UUID
    title: str
    source_section_path: str
    status: CandidateStatus
    suggested_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ArticleCandidateDetailResponse(ArticleCandidateResponse):
    fragments: list[ArticleCandidateFragmentResponse]


class StructureProposalResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    status: ProposalStatus
    candidate_count: int
    created_at: datetime
    updated_at: datetime
    candidates: list[ArticleCandidateResponse] = []

    model_config = {"from_attributes": True}


class StructureProposalDetailResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    status: ProposalStatus
    candidate_count: int
    created_at: datetime
    updated_at: datetime
    candidates: list[ArticleCandidateDetailResponse] = []

    model_config = {"from_attributes": True}
