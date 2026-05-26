import uuid

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.ingestion.types import ElementType
from app.domain.rag.retrieval import RetrievedBlock, is_retrievable_element
from app.domain.rag.types import CitationStatus, MessageRole
from app.models.article import Article, ArticleBlock
from app.models.block_citation import BlockCitation
from app.models.conversation import Conversation, Message
from app.models.source_fragment import SourceFragment


class RagRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_indexable_fragments(self, project_id: uuid.UUID) -> list[SourceFragment]:
        result = await self.db.execute(
            select(SourceFragment)
            .join(ArticleBlock, ArticleBlock.fragment_id == SourceFragment.id)
            .join(Article, Article.id == ArticleBlock.article_id)
            .where(Article.project_id == project_id)
            .options(selectinload(SourceFragment.source))
            .order_by(SourceFragment.source_id, SourceFragment.position_index)
            .distinct()
        )
        return [
            fragment
            for fragment in result.scalars().all()
            if is_retrievable_element(fragment.element_type, fragment.content)
        ]

    async def upsert_fragment_embedding(
        self,
        *,
        fragment: SourceFragment,
        embedding: list[float],
        embedding_model: str,
        content_hash: str,
    ) -> SourceFragment:
        fragment.embedding = embedding
        fragment.embedding_model = embedding_model
        fragment.embedding_dimension = len(embedding)
        fragment.embedding_content_hash = content_hash
        await self.db.flush()
        await self.db.refresh(fragment)
        return fragment

    async def count_project_embeddings(
        self,
        *,
        project_id: uuid.UUID,
        embedding_model: str,
    ) -> int:
        result = await self.db.execute(
            select(func.count(SourceFragment.id))
            .join(ArticleBlock, ArticleBlock.fragment_id == SourceFragment.id)
            .join(Article, Article.id == ArticleBlock.article_id)
            .where(
                Article.project_id == project_id,
                SourceFragment.embedding.is_not(None),
                SourceFragment.embedding_model == embedding_model,
            )
        )
        return int(result.scalar_one())

    async def retrieve_blocks(
        self,
        *,
        project_id: uuid.UUID,
        embedding: list[float],
        embedding_model: str,
        limit: int,
    ) -> list[RetrievedBlock]:
        result = await self.db.execute(
            text(
                """
                SELECT
                    ab.id AS block_id,
                    a.id AS article_id,
                    a.title AS article_title,
                    ab.fragment_id AS fragment_id,
                    s.title AS source_title,
                    s.filename AS source_filename,
                    ab.content AS content,
                    ab.element_type AS element_type,
                    ab.page_number AS page_number,
                    ab.section_path AS section_path,
                    1 - (sf.embedding <=> CAST(:query_embedding AS vector)) AS score
                FROM source_fragments sf
                JOIN article_blocks ab ON ab.fragment_id = sf.id
                JOIN articles a ON a.id = ab.article_id
                JOIN sources s ON s.id = sf.source_id
                WHERE a.project_id = :project_id
                  AND sf.embedding IS NOT NULL
                  AND sf.embedding_model = :embedding_model
                ORDER BY sf.embedding <=> CAST(:query_embedding AS vector)
                LIMIT :limit
                """
            ),
            {
                "project_id": project_id,
                "embedding_model": embedding_model,
                "query_embedding": _vector_literal(embedding),
                "limit": limit,
            },
        )
        return [
            RetrievedBlock(
                block_id=row["block_id"],
                article_id=row["article_id"],
                article_title=row["article_title"],
                fragment_id=row["fragment_id"],
                source_title=row["source_title"],
                source_filename=row["source_filename"],
                content=row["content"],
                element_type=_element_type(row["element_type"]),
                page_number=row["page_number"],
                section_path=row["section_path"],
                score=float(row["score"]),
            )
            for row in result.mappings().all()
            if is_retrievable_element(_element_type(row["element_type"]), row["content"])
        ]

    async def get_conversation(
        self,
        *,
        project_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.project_id == project_id,
            )
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def list_conversations(self, project_id: uuid.UUID) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.project_id == project_id)
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_conversation(
        self,
        *,
        project_id: uuid.UUID,
        title: str,
        user_id: str | None = None,
    ) -> Conversation:
        conversation = Conversation(
            project_id=project_id,
            title=title[:96],
            user_id=user_id,
        )
        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation

    async def add_message(
        self,
        *,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        meta_json: dict | None = None,
    ) -> Message:
        next_index = await self._next_message_position(conversation_id)
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            position_index=next_index,
            meta_json=meta_json,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        await self.touch_conversation(conversation_id)
        return message

    async def list_messages(
        self,
        *,
        project_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> list[Message]:
        conversation = await self.get_conversation(
            project_id=project_id,
            conversation_id=conversation_id,
        )
        if conversation is None:
            return []
        return list(conversation.messages)

    async def touch_conversation(self, conversation_id: uuid.UUID) -> None:
        conversation = await self.db.get(Conversation, conversation_id)
        if conversation is not None:
            conversation.updated_at = func.now()
            await self.db.flush()

    async def delete_conversation(
        self,
        *,
        project_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> bool:
        conversation = await self.get_conversation(
            project_id=project_id,
            conversation_id=conversation_id,
        )
        if conversation is None:
            return False
        await self.db.delete(conversation)
        await self.db.flush()
        return True

    async def save_block_citations(
        self,
        *,
        message_id: uuid.UUID,
        blocks: list[RetrievedBlock],
        confidence: float,
    ) -> list[BlockCitation]:
        rows = [
            BlockCitation(
                message_id=message_id,
                block_id=block.block_id,
                fragment_id=block.fragment_id,
                status=CitationStatus.UNVALIDATED,
                confidence=confidence,
                context=block.content,
            )
            for block in blocks
        ]
        self.db.add_all(rows)
        await self.db.flush()
        return rows

    async def _next_message_position(self, conversation_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.max(Message.position_index)).where(
                Message.conversation_id == conversation_id
            )
        )
        current = result.scalar_one_or_none()
        return 0 if current is None else int(current) + 1


def _vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(str(float(item)) for item in embedding) + "]"


def _element_type(value: str) -> ElementType:
    try:
        return ElementType[value]
    except KeyError:
        return ElementType(value)
