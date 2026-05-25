import uuid

from sqlalchemy import select

from app.application.ingestion.service import SAFE_INGESTION_ERROR, ingest_source
from app.domain.ingestion.types import ElementType, ExtractedElement
from app.domain.source import SourceStatus
from app.models.project import Project
from app.models.source import Source
from app.models.source_fragment import SourceFragment


async def test_ingest_source_creates_fragments(db, tmp_path, monkeypatch):
    project = Project(name="Ingestion Test")
    db.add(project)
    await db.flush()

    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n% test\n%%EOF\n")

    source = Source(
        project_id=project.id,
        filename="source.pdf",
        storage_path=str(pdf_path),
        status=SourceStatus.PENDING,
    )
    db.add(source)
    await db.flush()

    def fake_extract_pdf(file_path):
        assert file_path == str(pdf_path)
        return [
            ExtractedElement(
                content="Introduction",
                element_type=ElementType.HEADING,
                position_index=0,
                page_number=1,
                heading_level=1,
                section_path="Introduction",
            ),
            ExtractedElement(
                content="This is the first paragraph.",
                element_type=ElementType.PARAGRAPH,
                position_index=1,
                page_number=1,
                heading_level=None,
                section_path="Introduction",
            ),
        ]

    monkeypatch.setattr(
        "app.application.ingestion.service.extract_pdf",
        fake_extract_pdf,
    )

    result = await ingest_source(source.id, db)
    await db.commit()

    assert result is not None
    assert result.status == SourceStatus.DONE
    assert result.error_message is None
    assert result.title == "Introduction"

    fragments_result = await db.execute(
        select(SourceFragment)
        .where(SourceFragment.source_id == source.id)
        .order_by(SourceFragment.position_index)
    )
    fragments = list(fragments_result.scalars())

    assert len(fragments) == 2
    assert fragments[0].content == "Introduction"
    assert fragments[0].element_type == ElementType.HEADING
    assert fragments[0].position_index == 0
    assert fragments[1].content == "This is the first paragraph."
    assert fragments[1].element_type == ElementType.PARAGRAPH


async def test_ingest_source_marks_failed_when_extractor_fails(db, tmp_path, monkeypatch):
    project = Project(name="Failed Ingestion Test")
    db.add(project)
    await db.flush()

    pdf_path = tmp_path / "broken.pdf"
    pdf_path.write_bytes(b"not really a pdf")

    source = Source(
        project_id=project.id,
        filename="broken.pdf",
        storage_path=str(pdf_path),
        status=SourceStatus.PENDING,
    )
    db.add(source)
    await db.flush()

    def fake_extract_pdf(file_path):
        raise RuntimeError("extractor failed")

    monkeypatch.setattr(
        "app.application.ingestion.service.extract_pdf",
        fake_extract_pdf,
    )

    result = await ingest_source(source.id, db)
    await db.commit()

    assert result is not None
    assert result.status == SourceStatus.FAILED
    assert result.error_message == SAFE_INGESTION_ERROR
