import uuid
from pathlib import Path

from app.config import settings
from app.domain.ingestion.types import ElementType
from app.domain.source import SourceStatus
from app.domain.structure.types import CandidateStatus, ProposalStatus
from app.main import app
from app.models.article import Article, ArticleBlock
from app.models.article_candidate import ArticleCandidate, ArticleCandidateFragment
from app.models.source import Source
from app.models.source_fragment import SourceFragment
from app.models.structure_proposal import StructureProposal


async def test_upload_pdf_source_flow(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    project_response = await client.post(
        "/projects",
        json={"name": "Upload Test", "description": "Project for source upload"},
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    pdf_bytes = b"%PDF-1.4\n% fake pdf for upload test\n%%EOF\n"

    upload_response = await client.post(
        f"/projects/{project_id}/sources",
        files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_response.status_code == 202, upload_response.text

    source = upload_response.json()
    source_id = source["id"]

    assert source["project_id"] == project_id
    assert source["filename"] == "sample.pdf"
    assert source["status"] == "pending"

    stored_file = Path(settings.upload_dir) / project_id / f"{source_id}.pdf"
    assert stored_file.is_file()
    assert stored_file.read_bytes() == pdf_bytes
    assert app.state.arq_pool.jobs == [("ingest_source_job", (source_id,))]

    list_response = await client.get(f"/projects/{project_id}/sources")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == source_id


async def test_upload_rejects_non_pdf(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    project_response = await client.post("/projects", json={"name": "Upload Test"})
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    upload_response = await client.post(
        f"/projects/{project_id}/sources",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert upload_response.status_code == 400
    assert upload_response.json()["detail"] == "Only PDF files are supported"


async def test_upload_marks_source_failed_when_enqueue_fails(
    client,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    class FailingArqPool:
        async def enqueue_job(self, name: str, *args):
            raise RuntimeError("redis unavailable")

    app.state.arq_pool = FailingArqPool()

    project_response = await client.post("/projects", json={"name": "Queue Failure"})
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    upload_response = await client.post(
        f"/projects/{project_id}/sources",
        files={"file": ("sample.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")},
    )

    assert upload_response.status_code == 503
    assert upload_response.json()["detail"] == "Failed to enqueue source ingestion"

    sources_response = await client.get(f"/projects/{project_id}/sources")
    assert sources_response.status_code == 200
    sources = sources_response.json()
    assert len(sources) == 1
    assert sources[0]["status"] == "failed"
    assert sources[0]["error_message"] == "Failed to enqueue source ingestion"


async def test_source_detail_and_fragments_flow(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    project_response = await client.post("/projects", json={"name": "Fragment Test"})
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    upload_response = await client.post(
        f"/projects/{project_id}/sources",
        files={"file": ("sample.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")},
    )
    assert upload_response.status_code == 202
    source_id = upload_response.json()["id"]

    detail_response = await client.get(f"/projects/{project_id}/sources/{source_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == source_id

    empty_fragments_response = await client.get(
        f"/projects/{project_id}/sources/{source_id}/fragments"
    )
    assert empty_fragments_response.status_code == 200
    assert empty_fragments_response.json() == []

    db.add(
        SourceFragment(
            source_id=uuid.UUID(source_id),
            content="First extracted paragraph.",
            element_type=ElementType.PARAGRAPH,
            position_index=0,
            page_number=1,
        )
    )
    await db.commit()

    fragments_response = await client.get(
        f"/projects/{project_id}/sources/{source_id}/fragments"
    )
    assert fragments_response.status_code == 200
    assert fragments_response.json() == [
        {
            "id": fragments_response.json()[0]["id"],
            "source_id": source_id,
            "content": "First extracted paragraph.",
            "content_hash": None,
            "element_type": "paragraph",
            "position_index": 0,
            "page_number": 1,
            "heading_level": None,
            "section_path": None,
            "meta_json": None,
        }
    ]


async def test_delete_source_removes_source(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    project_response = await client.post("/projects", json={"name": "Delete Source"})
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    upload_response = await client.post(
        f"/projects/{project_id}/sources",
        files={"file": ("sample.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")},
    )
    assert upload_response.status_code == 202
    source_id = upload_response.json()["id"]
    stored_file = Path(settings.upload_dir) / project_id / f"{source_id}.pdf"
    assert stored_file.exists()

    delete_response = await client.delete(f"/projects/{project_id}/sources/{source_id}")
    assert delete_response.status_code == 204
    assert not stored_file.exists()

    sources_response = await client.get(f"/projects/{project_id}/sources")
    assert sources_response.status_code == 200
    assert sources_response.json() == []


async def test_delete_done_source_removes_derived_data(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    project_response = await client.post("/projects", json={"name": "Delete Done Source"})
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    source_id = uuid.uuid4()
    stored_file = Path(settings.upload_dir) / project_id / f"{source_id}.pdf"
    stored_file.parent.mkdir(parents=True, exist_ok=True)
    stored_file.write_bytes(b"%PDF-1.4\n%%EOF\n")

    source = Source(
        id=source_id,
        project_id=uuid.UUID(project_id),
        filename="done.pdf",
        storage_path=str(stored_file),
        status=SourceStatus.DONE,
    )
    db.add(source)
    await db.flush()

    fragment = SourceFragment(
        source_id=source.id,
        content="Built fragment.",
        element_type=ElementType.PARAGRAPH,
        position_index=0,
        page_number=1,
    )
    db.add(fragment)
    await db.flush()

    proposal = StructureProposal(
        project_id=uuid.UUID(project_id),
        status=ProposalStatus.REVIEWED,
        candidate_count=1,
    )
    db.add(proposal)
    await db.flush()

    candidate = ArticleCandidate(
        proposal_id=proposal.id,
        title="Built Article",
        source_section_path="Built Article",
        status=CandidateStatus.CONFIRMED,
        suggested_order=0,
    )
    db.add(candidate)
    await db.flush()

    db.add(
        ArticleCandidateFragment(
            candidate_id=candidate.id,
            fragment_id=fragment.id,
            position_index=0,
        )
    )
    article = Article(
        project_id=uuid.UUID(project_id),
        candidate_id=candidate.id,
        title="Built Article",
    )
    db.add(article)
    await db.flush()
    db.add(
        ArticleBlock(
            article_id=article.id,
            fragment_id=fragment.id,
            content=fragment.content,
            element_type=fragment.element_type,
            position_index=0,
            page_number=fragment.page_number,
        )
    )
    await db.commit()

    delete_response = await client.delete(f"/projects/{project_id}/sources/{source_id}")
    assert delete_response.status_code == 204, delete_response.text
    assert not stored_file.exists()

    sources_response = await client.get(f"/projects/{project_id}/sources")
    articles_response = await client.get(f"/projects/{project_id}/articles")
    proposals_response = await client.get(f"/projects/{project_id}/structure/proposals")

    assert sources_response.json() == []
    assert articles_response.json() == []
    assert proposals_response.json() == []


async def test_retry_source_queues_ingestion(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    project_response = await client.post("/projects", json={"name": "Retry Source"})
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    upload_response = await client.post(
        f"/projects/{project_id}/sources",
        files={"file": ("sample.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")},
    )
    assert upload_response.status_code == 202
    source_id = upload_response.json()["id"]

    app.state.arq_pool.jobs.clear()

    retry_response = await client.post(f"/projects/{project_id}/sources/{source_id}/retry")
    assert retry_response.status_code == 202
    assert retry_response.json()["status"] == "pending"
    assert app.state.arq_pool.jobs == [("ingest_source_job", (source_id,))]
