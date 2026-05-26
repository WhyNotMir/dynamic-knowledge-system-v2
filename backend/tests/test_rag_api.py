from app.domain.ingestion.types import ElementType
from app.domain.source import SourceStatus
from app.domain.structure.types import CandidateStatus, ProposalStatus
from app.integrations.llm.groq import GeneratedAnswer
from app.models.article import Article, ArticleBlock
from app.models.article_candidate import ArticleCandidate
from app.models.block_citation import BlockCitation
from app.models.project import Project
from app.models.source import Source
from app.models.source_fragment import SourceFragment
from app.models.structure_proposal import StructureProposal
from app.repositories.rag import RagRepository
from sqlalchemy import select


async def test_qa_without_articles_returns_insufficient_without_embedding_call(
    client,
    db,
    monkeypatch,
):
    project = Project(name="Empty QA Project")
    db.add(project)
    await db.commit()

    async def fail_embed_texts(texts: list[str]) -> list[list[float]]:
        raise AssertionError("empty projects should not call the embedding provider")

    monkeypatch.setattr("app.application.rag.service.embed_texts", fail_embed_texts)

    response = await client.post(
        f"/projects/{project.id}/ask",
        json={"question": "What does this project explain?"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["kind"] == "insufficient"
    assert body["answer"]["insufficientContext"] is True
    assert body["insufficientContext"]["reason"] == (
        "No indexed article fragments are available for this project."
    )


async def test_qa_indexes_articles_retrieves_context_and_returns_citations(
    client,
    db,
    monkeypatch,
):
    context_data = await _create_rag_context(db)

    async def embed_texts(texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, 0.0] for _ in texts]

    async def generate_answer(question: str, context: str) -> GeneratedAnswer:
        assert "Transformers use attention to route information." in context
        assert str(context_data["block"].id) in context
        return GeneratedAnswer(
            answer="Transformers use attention to route information.",
            points=["Attention connects the relevant tokens."],
            citation_block_ids=[str(context_data["block"].id)],
            confidence=0.82,
            insufficient_context=False,
        )

    monkeypatch.setattr("app.application.rag.service.embed_texts", embed_texts)
    monkeypatch.setattr("app.application.rag.qa_agent.generate_answer", generate_answer)

    response = await client.post(
        f"/projects/{context_data['project'].id}/ask",
        json={"question": "How do transformers route information?"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["kind"] == "answer"
    assert body["conversationId"] is not None
    assert body["messageId"] is not None
    assert body["answer"]["summary"] == "Transformers use attention to route information."
    assert body["answer"]["points"] == ["Attention connects the relevant tokens."]
    assert body["answer"]["confidence"] == 0.82
    assert body["answer"]["citations"] == [
        {
            "id": "1",
            "articleId": str(context_data["article"].id),
            "articleTitle": "Attention",
            "block": str(context_data["block"].id),
            "source": "attention.pdf",
            "page": 3,
            "sectionPath": "3 Model Architecture > 3.2 Attention",
            "fragment": str(context_data["fragment"].id),
            "quote": "Transformers use attention to route information.",
            "score": 1.0,
        }
    ]

    assert await RagRepository(db).count_project_embeddings(
        project_id=context_data["project"].id,
        embedding_model="text-embedding-3-small",
    ) == 1

    citations = list((await db.execute(select(BlockCitation))).scalars())
    assert len(citations) == 1
    assert citations[0].block_id == context_data["block"].id
    assert citations[0].fragment_id == context_data["fragment"].id


async def test_qa_suggestions_return_article_titles(client, db):
    context = await _create_rag_context(db)

    response = await client.get(f"/projects/{context['project'].id}/qa/suggestions")

    assert response.status_code == 200
    assert response.json() == ["What does Attention explain?"]


async def test_ask_creates_conversation_and_messages(client, db, monkeypatch):
    context_data = await _create_rag_context(db)

    async def embed_texts(texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, 0.0] for _ in texts]

    async def generate_answer(question: str, context: str) -> GeneratedAnswer:
        return GeneratedAnswer(
            answer="Transformers use attention to route information.",
            points=[],
            citation_block_ids=[str(context_data["block"].id)],
            confidence=0.9,
            insufficient_context=False,
        )

    monkeypatch.setattr("app.application.rag.service.embed_texts", embed_texts)
    monkeypatch.setattr("app.application.rag.qa_agent.generate_answer", generate_answer)

    ask_response = await client.post(
        f"/projects/{context_data['project'].id}/ask",
        json={"question": "How do transformers route information?"},
    )
    conversation_id = ask_response.json()["conversationId"]

    conversations_response = await client.get(
        f"/projects/{context_data['project'].id}/conversations"
    )
    assert conversations_response.status_code == 200
    assert conversations_response.json()[0]["id"] == conversation_id
    assert conversations_response.json()[0]["message_count"] == 2

    messages_response = await client.get(
        f"/projects/{context_data['project'].id}/conversations/{conversation_id}/messages"
    )
    assert [message["role"] for message in messages_response.json()] == ["user", "assistant"]
    assert messages_response.json()[1]["meta_json"]["confidence"] == 0.9


async def test_qa_uses_grounded_extractive_fallback_when_llm_citations_are_invalid(
    client,
    db,
    monkeypatch,
):
    context_data = await _create_rag_context(db)

    async def embed_texts(texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, 0.0] for _ in texts]

    async def generate_answer(question: str, context: str) -> GeneratedAnswer:
        return GeneratedAnswer(
            answer="Transformers use attention to route information.",
            points=[],
            citation_block_ids=["not-a-real-block-id"],
            confidence=0.9,
            insufficient_context=False,
        )

    monkeypatch.setattr("app.application.rag.service.embed_texts", embed_texts)
    monkeypatch.setattr("app.application.rag.qa_agent.generate_answer", generate_answer)

    response = await client.post(
        f"/projects/{context_data['project'].id}/ask",
        json={"question": "How do transformers route information?"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["kind"] == "answer"
    assert body["answer"]["summary"] == "Transformers use attention to route information."
    assert body["answer"]["insufficientContext"] is False
    assert body["answer"]["citations"][0]["block"] == str(context_data["block"].id)


async def _create_rag_context(db):
    project = Project(name="RAG Test Project")
    db.add(project)
    await db.flush()

    source = Source(
        project_id=project.id,
        filename="attention.pdf",
        storage_path="/tmp/attention.pdf",
        status=SourceStatus.DONE,
    )
    db.add(source)
    await db.flush()

    fragment = SourceFragment(
        source_id=source.id,
        content="Transformers use attention to route information.",
        element_type=ElementType.PARAGRAPH,
        position_index=0,
        page_number=3,
        section_path="3 Model Architecture > 3.2 Attention",
    )
    db.add(fragment)
    await db.flush()

    proposal = StructureProposal(
        project_id=project.id,
        status=ProposalStatus.REVIEWED,
        candidate_count=1,
    )
    db.add(proposal)
    await db.flush()

    candidate = ArticleCandidate(
        proposal_id=proposal.id,
        title="Attention",
        source_section_path="3 Model Architecture > 3.2 Attention",
        status=CandidateStatus.CONFIRMED,
        suggested_order=0,
    )
    db.add(candidate)
    await db.flush()

    article = Article(
        project_id=project.id,
        candidate_id=candidate.id,
        title="Attention",
    )
    db.add(article)
    await db.flush()

    block = ArticleBlock(
        article_id=article.id,
        fragment_id=fragment.id,
        content=fragment.content,
        element_type=fragment.element_type,
        position_index=0,
        page_number=fragment.page_number,
        heading_level=fragment.heading_level,
        section_path=fragment.section_path,
        meta_json=fragment.meta_json,
    )
    db.add(block)
    await db.commit()

    return {
        "project": project,
        "source": source,
        "fragment": fragment,
        "proposal": proposal,
        "candidate": candidate,
        "article": article,
        "block": block,
    }
