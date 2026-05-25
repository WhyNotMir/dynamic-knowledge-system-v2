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
    source_title: str | None
    source_filename: str
    content: str
    element_type: ElementType
    position_index: int
    page_number: int | None
    heading_level: int | None
    section_path: str | None
    meta_json: dict | None
    include_in_article: bool = True
    include_in_outline: bool = True
    created_at: datetime


class ArticleResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    candidate_id: uuid.UUID
    title: str
    topic_path: list[str]
    block_count: int
    source_count: int
    status: ArticleStatus
    created_at: datetime
    updated_at: datetime


class ArticleDetailResponse(ArticleResponse):
    blocks: list[ArticleBlockResponse]
