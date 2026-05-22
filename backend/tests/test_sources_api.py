import uuid
from pathlib import Path

from app.config import settings
from app.domain.ingestion.types import ElementType
from app.main import app
from app.models.source_fragment import SourceFragment


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
