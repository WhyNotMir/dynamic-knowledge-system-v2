from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from loguru import logger

from app.domain.rag.retrieval import RetrievedBlock
from app.integrations.embeddings.openai import EmbeddingProviderNotConfiguredError
from app.integrations.llm.groq import LlmProviderNotConfiguredError, generate_answer


MAX_CITATIONS = 5


@dataclass(frozen=True)
class AgentAnswer:
    answer: str
    points: list[str]
    cited_blocks: list[RetrievedBlock]
    confidence: float
    insufficient_context: bool


async def answer_from_context(
    *,
    question: str,
    blocks: list[RetrievedBlock],
) -> AgentAnswer:
    try:
        generated = await generate_answer(
            question=question,
            context=_context_text(blocks),
        )
    except (EmbeddingProviderNotConfiguredError, LlmProviderNotConfiguredError) as exc:
        logger.warning("Q&A LLM provider is not configured: {}", exc)
        return _extractive_answer(blocks)
    except Exception as exc:
        logger.exception("Q&A LLM answer generation failed: {}", exc)
        return _extractive_answer(blocks)

    by_id = {str(block.block_id): block for block in blocks}
    cited_blocks = [
        by_id[block_id]
        for block_id in generated.citation_block_ids
        if _valid_uuid(block_id) and block_id in by_id
    ][:MAX_CITATIONS]
    confidence = _clamp_confidence(generated.confidence)

    if generated.insufficient_context:
        return AgentAnswer(
            answer=generated.answer,
            points=generated.points,
            cited_blocks=[],
            confidence=min(confidence, 0.34),
            insufficient_context=True,
        )

    if not cited_blocks:
        logger.warning("Q&A LLM answer had no valid citations; using extractive fallback")
        return _extractive_answer(blocks)

    if not _citations_overlap(generated.answer, cited_blocks):
        logger.warning("Q&A LLM answer citations did not overlap evidence; using extractive fallback")
        return _extractive_answer(blocks)

    return AgentAnswer(
        answer=generated.answer,
        points=generated.points,
        cited_blocks=cited_blocks,
        confidence=confidence,
        insufficient_context=False,
    )


def _context_text(blocks: list[RetrievedBlock]) -> str:
    lines: list[str] = []
    for block in blocks:
        source = block.source_title or block.source_filename
        page = f"p.{block.page_number}" if block.page_number else "page unknown"
        section = block.section_path or "section unknown"
        lines.append(
            "\n".join(
                [
                    f"block_id: {block.block_id}",
                    f"article_id: {block.article_id}",
                    f"article_title: {block.article_title}",
                    f"source: {source}",
                    f"page: {page}",
                    f"section: {section}",
                    f"score: {block.score:.4f}",
                    f"content: {block.content}",
                ]
            )
        )
    return "\n\n---\n\n".join(lines)


def _unavailable_answer(blocks: list[RetrievedBlock]) -> AgentAnswer:
    return AgentAnswer(
        answer="The answer could not be generated from the retrieved evidence.",
        points=[],
        cited_blocks=blocks[:MAX_CITATIONS],
        confidence=0.0,
        insufficient_context=True,
    )


def _extractive_answer(blocks: list[RetrievedBlock]) -> AgentAnswer:
    if not blocks:
        return _unavailable_answer(blocks)

    best_block = blocks[0]
    answer = _first_sentence(best_block.content) or best_block.content
    return AgentAnswer(
        answer=answer,
        points=[],
        cited_blocks=blocks[:MAX_CITATIONS],
        confidence=max(0.35, min(0.72, best_block.score)),
        insufficient_context=False,
    )


def _clamp_confidence(value: float) -> float:
    return max(0.0, min(1.0, value))


def _valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def _citations_overlap(answer: str, blocks: list[RetrievedBlock]) -> bool:
    answer_terms = _terms(answer)
    if not answer_terms:
        return False
    evidence_terms = set()
    for block in blocks:
        evidence_terms.update(_terms(block.content))
    return bool(answer_terms & evidence_terms)


def _terms(value: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-zA-Z0-9_]{4,}", value.lower())
        if term not in {"that", "this", "with", "from", "there", "their"}
    }


def _first_sentence(value: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        return ""

    match = re.search(r"(?<=[.!?])\s+", normalized)
    if match is None:
        return normalized
    return normalized[: match.start()].strip()
