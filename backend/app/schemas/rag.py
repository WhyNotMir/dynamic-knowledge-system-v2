import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class AskQuestionRequest(BaseModel):
    question: str = Field(min_length=1)
    conversation_id: uuid.UUID | None = Field(default=None, alias="conversationId")
    top_k: int | None = Field(default=None, alias="topK", ge=1, le=50)
    max_per_article: int | None = Field(default=None, alias="maxPerArticle", ge=1, le=10)
    min_score: float | None = Field(default=None, alias="minScore", ge=0, le=1)
    min_evidence_score: float | None = Field(default=None, alias="minEvidenceScore", ge=0, le=1)
    min_evidence_blocks: int | None = Field(default=None, alias="minEvidenceBlocks", ge=1, le=10)

    model_config = {"populate_by_name": True}

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Question must not be blank")
        return stripped


class CitationResponse(BaseModel):
    id: str
    articleId: uuid.UUID
    articleTitle: str
    block: uuid.UUID
    source: str
    page: int
    sectionPath: str | None = None
    fragment: uuid.UUID
    quote: str
    score: float


class QAAnswerResponse(BaseModel):
    summary: str
    points: list[str]
    citations: list[CitationResponse]
    confidence: float
    insufficientContext: bool = False


class InsufficientContextResponse(BaseModel):
    reason: str
    suggestions: list[str]
    pendingSources: list[str] = []


class QAMessageResponse(BaseModel):
    kind: str
    text: str | None = None
    conversationId: uuid.UUID | None = None
    messageId: uuid.UUID | None = None
    answer: QAAnswerResponse | None = None
    insufficientContext: InsufficientContextResponse | None = None


class ConversationResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    summary: str | None = None
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    position_index: int
    meta_json: dict | None = None
    created_at: datetime
