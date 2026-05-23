import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domain.ingestion.types import ElementType
from app.domain.source import SourceStatus


class SourceResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    filename: str
    title: str | None = None
    status: SourceStatus
    fragment_count: int = 0
    page_count: int = 0
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceFragmentResponse(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    content: str
    content_hash: str | None = None
    element_type: ElementType
    position_index: int
    page_number: int | None = None
    heading_level: int | None = None
    section_path: str | None = None
    meta_json: dict | None = None

    model_config = {"from_attributes": True}
