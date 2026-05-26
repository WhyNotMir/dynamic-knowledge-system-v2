from __future__ import annotations

import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domain.rag.retrieval import (
    RetrievalSettings,
    RetrievedBlock,
    diversify_results,
    has_enough_evidence,
    normalized_retrieval_text,
    retrieval_content_hash,
)
from app.domain.rag.types import MessageRole
from app.domain.source import SourceStatus
from app.integrations.embeddings.openai import embed_texts
from app.repositories.articles import ArticleRepository
from app.repositories.projects import ProjectRepository
from app.repositories.rag import RagRepository
from app.repositories.sources import SourceRepository
from app.application.rag.qa_agent import AgentAnswer, answer_from_context


class ProjectNotFoundError(RuntimeError):
    pass


class ConversationNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class Citation:
    id: str
    article_id: uuid.UUID
    article_title: str
    block_id: uuid.UUID
    source: str
    page: int
    section_path: str | None
    fragment_id: uuid.UUID
    quote: str
    score: float


@dataclass(frozen=True)
class QAAnswer:
    answer: str
    points: list[str]
    citations: list[Citation]
    confidence: float
    insufficient_context: bool


@dataclass(frozen=True)
class InsufficientContext:
    reason: str
    suggestions: list[str]
    pending_sources: list[str]


@dataclass(frozen=True)
class AskResult:
    conversation_id: uuid.UUID
    user_message_id: uuid.UUID
    assistant_message_id: uuid.UUID
    answer: QAAnswer
    insufficient_context: InsufficientContext | None = None


class AskState(TypedDict, total=False):
    project_id: uuid.UUID
    question: str
    cleaned_question: str
    conversation_id: uuid.UUID | None
    db: AsyncSession
    retrieval_overrides: dict
    retrieval_settings: RetrievalSettings
    retrieved: list[RetrievedBlock]
    agent_answer: AgentAnswer
    insufficient_context: InsufficientContext
    result: AskResult


async def run_ask(
    *,
    project_id: uuid.UUID,
    question: str,
    db: AsyncSession,
    conversation_id: uuid.UUID | None = None,
    retrieval_overrides: dict | None = None,
) -> AskResult:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")
    if conversation_id is not None:
        conversation = await RagRepository(db).get_conversation(
            project_id=project_id,
            conversation_id=conversation_id,
        )
        if conversation is None:
            raise ConversationNotFoundError("Conversation not found")

    state = await _qa_graph().ainvoke(
        {
            "project_id": project_id,
            "question": question,
            "conversation_id": conversation_id,
            "db": db,
            "retrieval_overrides": retrieval_overrides or {},
        }
    )
    return state["result"]


async def index_project_source_fragments(
    *,
    project_id: uuid.UUID,
    db: AsyncSession,
) -> int:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    rag = RagRepository(db)
    fragments = await rag.list_indexable_fragments(project_id)
    pending = []
    pending_hashes: list[str] = []
    for fragment in fragments:
        content_hash = retrieval_content_hash(fragment.content)
        if (
            fragment.embedding is not None
            and fragment.embedding_model == settings.embedding_model
            and fragment.embedding_content_hash == content_hash
        ):
            continue
        pending.append(fragment)
        pending_hashes.append(content_hash)

    if not pending:
        return 0

    vectors = await embed_texts([fragment.content for fragment in pending])
    for fragment, vector, content_hash in zip(pending, vectors, pending_hashes):
        await rag.upsert_fragment_embedding(
            fragment=fragment,
            embedding=vector,
            embedding_model=settings.embedding_model,
            content_hash=content_hash,
        )
    return len(pending)


async def suggest_questions(project_id: uuid.UUID, db: AsyncSession) -> list[str]:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    articles = await ArticleRepository(db).list_by_project(project_id)
    titles = [article.title for article in articles[:3]]
    return [f"What does {title} explain?" for title in titles]


async def list_conversations(project_id: uuid.UUID, db: AsyncSession):
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")
    return await RagRepository(db).list_conversations(project_id)


async def list_conversation_messages(
    *,
    project_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: AsyncSession,
):
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")
    conversation = await RagRepository(db).get_conversation(
        project_id=project_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise ConversationNotFoundError("Conversation not found")
    return list(conversation.messages)


async def delete_conversation(
    *,
    project_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")
    return await RagRepository(db).delete_conversation(
        project_id=project_id,
        conversation_id=conversation_id,
    )


async def _retrieve_context(state: AskState) -> AskState:
    db = state["db"]
    project_id = state["project_id"]
    question = normalized_retrieval_text(state["question"])
    retrieval_settings = await _retrieval_settings(project_id, db, state["retrieval_overrides"])

    if not question:
        return {
            "cleaned_question": question,
            "retrieval_settings": retrieval_settings,
            "retrieved": [],
            "insufficient_context": InsufficientContext(
                reason="Ask a non-empty question.",
                suggestions=[],
                pending_sources=[],
            ),
        }

    await index_project_source_fragments(project_id=project_id, db=db)
    rag = RagRepository(db)
    if await rag.count_project_embeddings(
        project_id=project_id,
        embedding_model=settings.embedding_model,
    ) == 0:
        return {
            "cleaned_question": question,
            "retrieval_settings": retrieval_settings,
            "retrieved": [],
            "insufficient_context": InsufficientContext(
                reason="No indexed article fragments are available for this project.",
                suggestions=await suggest_questions(project_id, db),
                pending_sources=await _pending_sources(project_id, db),
            ),
        }

    query_embedding = (await embed_texts([question]))[0]
    raw_results = await rag.retrieve_blocks(
        project_id=project_id,
        embedding=query_embedding,
        embedding_model=settings.embedding_model,
        limit=max(retrieval_settings.top_k * 4, retrieval_settings.top_k),
    )
    retrieved = diversify_results(
        raw_results,
        top_k=retrieval_settings.top_k,
        max_per_article=retrieval_settings.max_per_article,
        min_score=retrieval_settings.min_score,
    )
    if not retrieved:
        return {
            "cleaned_question": question,
            "retrieval_settings": retrieval_settings,
            "retrieved": [],
            "insufficient_context": InsufficientContext(
                reason="No indexed article fragments matched the question.",
                suggestions=await suggest_questions(project_id, db),
                pending_sources=await _pending_sources(project_id, db),
            ),
        }
    if not has_enough_evidence(
        retrieved,
        min_evidence_score=retrieval_settings.min_evidence_score,
        min_evidence_blocks=retrieval_settings.min_evidence_blocks,
    ):
        return {
            "cleaned_question": question,
            "retrieval_settings": retrieval_settings,
            "retrieved": retrieved,
            "insufficient_context": InsufficientContext(
                reason="The retrieved evidence is too weak for a reliable answer.",
                suggestions=await suggest_questions(project_id, db),
                pending_sources=await _pending_sources(project_id, db),
            ),
        }

    return {
        "cleaned_question": question,
        "retrieval_settings": retrieval_settings,
        "retrieved": retrieved,
    }


def _route_after_retrieve(state: AskState) -> str:
    return "persist" if "insufficient_context" in state else "answer"


async def _answer_from_context(state: AskState) -> AskState:
    agent_answer = await answer_from_context(
        question=state["cleaned_question"],
        blocks=state["retrieved"],
    )
    if agent_answer.insufficient_context:
        return {
            "agent_answer": agent_answer,
            "insufficient_context": InsufficientContext(
                reason=agent_answer.answer,
                suggestions=await suggest_questions(state["project_id"], state["db"]),
                pending_sources=await _pending_sources(state["project_id"], state["db"]),
            ),
        }
    return {"agent_answer": agent_answer}


async def _persist_answer(state: AskState) -> AskState:
    db = state["db"]
    project_id = state["project_id"]
    rag = RagRepository(db)
    conversation_id = state.get("conversation_id")
    if conversation_id is None:
        conversation = await rag.create_conversation(
            project_id=project_id,
            title=_conversation_title(state["cleaned_question"] or state["question"]),
        )
    else:
        conversation = await rag.get_conversation(
            project_id=project_id,
            conversation_id=conversation_id,
        )
        if conversation is None:
            raise ConversationNotFoundError("Conversation not found")

    user_message = await rag.add_message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=state["question"],
    )
    if "agent_answer" in state:
        answer = state["agent_answer"]
        citations = [_citation_from_block(str(index), block) for index, block in enumerate(answer.cited_blocks, 1)]
        qa_answer = QAAnswer(
            answer=answer.answer,
            points=answer.points,
            citations=citations,
            confidence=answer.confidence,
            insufficient_context=answer.insufficient_context,
        )
        insufficient = state.get("insufficient_context")
        cited_blocks = answer.cited_blocks
    else:
        insufficient = state["insufficient_context"]
        cited_blocks = []
        qa_answer = QAAnswer(
            answer="There is not enough information in the indexed articles to answer reliably.",
            points=[],
            citations=[],
            confidence=0.0,
            insufficient_context=True,
        )

    assistant_message = await rag.add_message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=qa_answer.answer,
        meta_json={
            "citations": [_stored_citation(citation) for citation in qa_answer.citations],
            "confidence": qa_answer.confidence,
            "insufficient_context": qa_answer.insufficient_context,
        },
    )
    if cited_blocks:
        await rag.save_block_citations(
            message_id=assistant_message.id,
            blocks=cited_blocks,
            confidence=qa_answer.confidence,
        )

    return {
        "result": AskResult(
            conversation_id=conversation.id,
            user_message_id=user_message.id,
            assistant_message_id=assistant_message.id,
            answer=qa_answer,
            insufficient_context=insufficient,
        )
    }


@lru_cache(maxsize=1)
def _qa_graph():
    graph = StateGraph(AskState)
    graph.add_node("retrieve_context", _retrieve_context)
    graph.add_node("answer_from_context", _answer_from_context)
    graph.add_node("persist_answer", _persist_answer)

    graph.set_entry_point("retrieve_context")
    graph.add_conditional_edges(
        "retrieve_context",
        _route_after_retrieve,
        {
            "answer": "answer_from_context",
            "persist": "persist_answer",
        },
    )
    graph.add_edge("answer_from_context", "persist_answer")
    graph.add_edge("persist_answer", END)
    return graph.compile()


async def _retrieval_settings(
    project_id: uuid.UUID,
    db: AsyncSession,
    overrides: dict,
) -> RetrievalSettings:
    project = await ProjectRepository(db).get(project_id)
    project_qa = {}
    if project is not None and isinstance(project.settings, dict):
        raw = project.settings.get("qa")
        if isinstance(raw, dict):
            project_qa = raw
    merged = {**project_qa, **{key: value for key, value in overrides.items() if value is not None}}
    base = RetrievalSettings()
    return RetrievalSettings(
        top_k=_int_setting(merged.get("top_k"), base.top_k, minimum=1, maximum=50),
        max_per_article=_int_setting(
            merged.get("max_per_article"),
            base.max_per_article,
            minimum=1,
            maximum=10,
        ),
        min_score=_float_setting(merged.get("min_score"), base.min_score, minimum=0.0, maximum=1.0),
        min_evidence_score=_float_setting(
            merged.get("min_evidence_score"),
            base.min_evidence_score,
            minimum=0.0,
            maximum=1.0,
        ),
        min_evidence_blocks=_int_setting(
            merged.get("min_evidence_blocks"),
            base.min_evidence_blocks,
            minimum=1,
            maximum=10,
        ),
    )


async def _pending_sources(project_id: uuid.UUID, db: AsyncSession) -> list[str]:
    sources = await SourceRepository(db).list_by_project(project_id)
    return [
        source.title or source.filename
        for source in sources
        if source.status in {SourceStatus.PENDING, SourceStatus.PROCESSING}
    ]


def _conversation_title(question: str) -> str:
    title = normalized_retrieval_text(question)
    return title[:96] or "New question"


def _citation_from_block(index: str, block: RetrievedBlock) -> Citation:
    return Citation(
        id=index,
        article_id=block.article_id,
        article_title=block.article_title,
        block_id=block.block_id,
        source=block.source_title or block.source_filename,
        page=block.page_number or 0,
        section_path=block.section_path,
        fragment_id=block.fragment_id,
        quote=block.content,
        score=block.score,
    )


def _stored_citation(citation: Citation) -> dict:
    return {
        "id": citation.id,
        "articleId": str(citation.article_id),
        "articleTitle": citation.article_title,
        "block": str(citation.block_id),
        "source": citation.source,
        "page": citation.page,
        "sectionPath": citation.section_path,
        "fragment": str(citation.fragment_id),
        "quote": citation.quote,
        "score": citation.score,
    }


def _int_setting(value, default: int, *, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def _float_setting(value, default: float, *, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))
