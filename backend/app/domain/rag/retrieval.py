from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

from app.domain.ingestion.types import ElementType


RETRIEVABLE_ELEMENT_TYPES = frozenset(
    {
        ElementType.PARAGRAPH,
        ElementType.LIST_ITEM,
        ElementType.TABLE,
        ElementType.CAPTION,
        ElementType.QUOTE,
        ElementType.CODE_BLOCK,
        ElementType.FOOTNOTE,
    }
)


@dataclass(frozen=True)
class RetrievedBlock:
    block_id: uuid.UUID
    article_id: uuid.UUID
    article_title: str
    fragment_id: uuid.UUID
    source_title: str | None
    source_filename: str
    content: str
    element_type: ElementType
    page_number: int | None
    section_path: str | None
    score: float


@dataclass(frozen=True)
class RetrievalSettings:
    top_k: int = 15
    max_per_article: int = 3
    min_score: float = 0.2
    min_evidence_score: float = 0.32
    min_evidence_blocks: int = 1


def normalized_retrieval_text(value: str) -> str:
    return " ".join(value.split()).strip()


def retrieval_content_hash(value: str) -> str:
    return hashlib.sha256(normalized_retrieval_text(value).encode("utf-8")).hexdigest()


def is_retrievable_element(element_type: ElementType, content: str) -> bool:
    return element_type in RETRIEVABLE_ELEMENT_TYPES and bool(normalized_retrieval_text(content))


def diversify_results(
    results: list[RetrievedBlock],
    *,
    top_k: int,
    max_per_article: int,
    min_score: float,
) -> list[RetrievedBlock]:
    if top_k <= 0 or max_per_article <= 0:
        return []

    selected: list[RetrievedBlock] = []
    per_article: dict[uuid.UUID, int] = {}

    for result in results:
        if result.score < min_score:
            continue
        count = per_article.get(result.article_id, 0)
        if count >= max_per_article:
            continue

        selected.append(result)
        per_article[result.article_id] = count + 1
        if len(selected) >= top_k:
            break

    return selected


def has_enough_evidence(
    results: list[RetrievedBlock],
    *,
    min_evidence_score: float,
    min_evidence_blocks: int,
) -> bool:
    if min_evidence_blocks <= 0:
        return True
    return sum(1 for result in results if result.score >= min_evidence_score) >= min_evidence_blocks
