from __future__ import annotations

import hashlib
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.ingestion.extractor import extract_pdf
from app.domain.source import SourceStatus
from app.models.source import Source
from app.models.source_fragment import SourceFragment
from app.repositories.sources import SourceRepository


def content_hash(content: str) -> str:
    normalized = " ".join(content.split()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def ingest_source(source_id: uuid.UUID, db: AsyncSession) -> Source | None:
    sources = SourceRepository(db)
    source = await sources.get(source_id)
    if source is None:
        return None

    await sources.update_status(source, SourceStatus.PROCESSING, None)

    try:
        elements = extract_pdf(source.storage_path)

        fragments = [
            SourceFragment(
                source_id=source.id,
                content=element.content,
                content_hash=content_hash(element.content),
                element_type=element.element_type,
                position_index=element.position_index,
                page_number=element.page_number,
                heading_level=element.heading_level,
                section_path=element.section_path,
                meta_json=element.meta_json,
            )
            for element in elements
            if element.content.strip()
        ]

        await sources.replace_fragments(source.id, fragments)

        return await sources.update_status(
            source,
            SourceStatus.DONE,
            None,
        )

    except Exception as exc:
        return await sources.update_status(
            source,
            SourceStatus.FAILED,
            str(exc),
        )
