import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.rag.service import (
    AskResult,
    ConversationNotFoundError,
    ProjectNotFoundError,
    delete_conversation,
    list_conversation_messages,
    list_conversations,
    run_ask,
    suggest_questions,
)
from app.database import get_db
from app.integrations.embeddings.openai import EmbeddingProviderNotConfiguredError
from app.integrations.llm.groq import LlmProviderNotConfiguredError
from app.schemas.rag import (
    AskQuestionRequest,
    CitationResponse,
    ConversationMessageResponse,
    ConversationResponse,
    InsufficientContextResponse,
    QAAnswerResponse,
    QAMessageResponse,
)


router = APIRouter(prefix="/projects/{project_id}", tags=["qa"])


@router.post("/ask", response_model=QAMessageResponse)
async def ask_project_question(
    project_id: uuid.UUID,
    payload: AskQuestionRequest,
    db: AsyncSession = Depends(get_db),
) -> QAMessageResponse:
    try:
        result = await run_ask(
            project_id=project_id,
            question=payload.question,
            conversation_id=payload.conversation_id,
            retrieval_overrides=_retrieval_overrides(payload),
            db=db,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (EmbeddingProviderNotConfiguredError, LlmProviderNotConfiguredError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    await db.commit()
    return _ask_result_response(result)


@router.post("/ask/stream")
async def ask_project_question_stream(
    project_id: uuid.UUID,
    payload: AskQuestionRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    return StreamingResponse(
        _ask_stream(project_id, payload, db),
        media_type="text/event-stream",
    )


@router.get("/qa/suggestions", response_model=list[str])
@router.get("/ask/suggestions", response_model=list[str])
async def list_qa_suggestions(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    try:
        return await suggest_questions(project_id, db)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/conversations", response_model=list[ConversationResponse])
async def get_project_conversations(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ConversationResponse]:
    try:
        conversations = await list_conversations(project_id, db)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        ConversationResponse(
            id=conversation.id,
            project_id=conversation.project_id,
            title=conversation.title,
            summary=conversation.summary,
            message_count=len(conversation.messages),
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
        for conversation in conversations
    ]


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[ConversationMessageResponse],
)
async def get_conversation_messages(
    project_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ConversationMessageResponse]:
    try:
        messages = await list_conversation_messages(
            project_id=project_id,
            conversation_id=conversation_id,
            db=db,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        ConversationMessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role.value,
            content=message.content,
            position_index=message.position_index,
            meta_json=message.meta_json,
            created_at=message.created_at,
        )
        for message in messages
    ]


@router.delete("/conversations/{conversation_id}", status_code=204)
async def remove_conversation(
    project_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        deleted = await delete_conversation(
            project_id=project_id,
            conversation_id=conversation_id,
            db=db,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.commit()


async def _ask_stream(
    project_id: uuid.UUID,
    payload: AskQuestionRequest,
    db: AsyncSession,
) -> AsyncIterator[str]:
    yield _sse("status", {"status": "retrieving"})
    try:
        yield _sse("status", {"status": "answering"})
        result = await run_ask(
            project_id=project_id,
            question=payload.question,
            conversation_id=payload.conversation_id,
            retrieval_overrides=_retrieval_overrides(payload),
            db=db,
        )
        await db.commit()
        response = _ask_result_response(result).model_dump(mode="json")
        status = "insufficient" if response["kind"] == "insufficient" else "answering"
        yield _sse("status", {"status": status})
        yield _sse("answer", response)
        yield _sse("done", {"status": "done"})
    except (ProjectNotFoundError, ConversationNotFoundError) as exc:
        yield _sse("error", {"status": 404, "detail": str(exc)})
    except (EmbeddingProviderNotConfiguredError, LlmProviderNotConfiguredError) as exc:
        yield _sse("error", {"status": 503, "detail": str(exc)})


def _ask_result_response(result: AskResult) -> QAMessageResponse:
    kind = "insufficient" if result.answer.insufficient_context else "answer"
    return QAMessageResponse(
        kind=kind,
        conversationId=result.conversation_id,
        messageId=result.assistant_message_id,
        answer=QAAnswerResponse(
            summary=result.answer.answer,
            points=result.answer.points,
            confidence=result.answer.confidence,
            insufficientContext=result.answer.insufficient_context,
            citations=[
                CitationResponse(
                    id=citation.id,
                    articleId=citation.article_id,
                    articleTitle=citation.article_title,
                    block=citation.block_id,
                    source=citation.source,
                    page=citation.page,
                    sectionPath=citation.section_path,
                    fragment=citation.fragment_id,
                    quote=citation.quote,
                    score=citation.score,
                )
                for citation in result.answer.citations
            ],
        ),
        insufficientContext=(
            InsufficientContextResponse(
                reason=result.insufficient_context.reason,
                suggestions=result.insufficient_context.suggestions,
                pendingSources=result.insufficient_context.pending_sources,
            )
            if result.insufficient_context is not None
            else None
        ),
    )


def _retrieval_overrides(payload: AskQuestionRequest) -> dict:
    return {
        "top_k": payload.top_k,
        "max_per_article": payload.max_per_article,
        "min_score": payload.min_score,
        "min_evidence_score": payload.min_evidence_score,
        "min_evidence_blocks": payload.min_evidence_blocks,
    }


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"
