import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domain.articles.types import ArticleStatus
from app.domain.ingestion.types import ElementType


class BuildArticlesRequest(BaseModel):
    proposal_id: uuid.UUID


class ArticleBlockResponse(BaseModel):
    id: uuid.UUID
    article_id: uuid.UUID
    fragment_id: uuid.UUID
    content: str
    element_type: ElementType
    position_index: int
    page_number: int | None
    heading_level: int | None
    section_path: str | None
    meta_json: dict | None
    created_at: datetime


class ArticleResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    candidate_id: uuid.UUID
    title: str
    status: ArticleStatus
    created_at: datetime
    updated_at: datetime


class ArticleDetailResponse(ArticleResponse):
    blocks: list[ArticleBlockResponse]
