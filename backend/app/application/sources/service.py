import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domain.source import SourceStatus
from app.models.source import Source
from app.models.source_fragment import SourceFragment
from app.repositories.articles import ArticleRepository
from app.repositories.projects import ProjectRepository
from app.repositories.sources import SourceRepository
from app.repositories.structure import StructureRepository


class ProjectNotFoundError(RuntimeError):
    pass


class UnsupportedSourceTypeError(RuntimeError):
    pass


class SourceNotFoundError(RuntimeError):
    pass


def ensure_pdf(filename: str) -> None:
    if not filename.lower().endswith(".pdf"):
        raise UnsupportedSourceTypeError("Only PDF files are supported")


async def create_uploaded_source(
    project_id: uuid.UUID,
    filename: str | None,
    read_chunk: Callable[[int], Awaitable[bytes]],
    db: AsyncSession,
) -> Source:
    if not filename:
        raise UnsupportedSourceTypeError("File name is required")

    ensure_pdf(filename)

    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    source_id = uuid.uuid4()
    project_dir = Path(settings.upload_dir) / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)

    storage_path = project_dir / f"{source_id}.pdf"

    async with aiofiles.open(storage_path, "wb") as out:
        while chunk := await read_chunk(1024 * 1024):
            await out.write(chunk)

    return await SourceRepository(db).create(
        source_id=source_id,
        project_id=project_id,
        filename=filename,
        storage_path=str(storage_path),
    )


async def list_project_sources(project_id: uuid.UUID, db: AsyncSession) -> list[Source]:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    return await SourceRepository(db).list_by_project(project_id)


async def get_project_source(
    project_id: uuid.UUID,
    source_id: uuid.UUID,
    db: AsyncSession,
) -> Source:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    source = await SourceRepository(db).get_by_project(project_id, source_id)
    if source is None:
        raise SourceNotFoundError("Source not found")
    return source


async def list_source_fragments(
    project_id: uuid.UUID,
    source_id: uuid.UUID,
    db: AsyncSession,
) -> list[SourceFragment]:
    await get_project_source(project_id, source_id, db)

    return await SourceRepository(db).list_fragments(source_id)


async def delete_project_source(
    project_id: uuid.UUID,
    source_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    source = await get_project_source(project_id, source_id, db)
    storage_path = Path(source.storage_path)
    await ArticleRepository(db).delete_for_source(
        project_id=project_id,
        source_id=source_id,
    )
    await StructureRepository(db).delete_candidates_for_source(
        project_id=project_id,
        source_id=source_id,
    )
    await SourceRepository(db).delete(source)
    if storage_path.exists():
        storage_path.unlink()


async def prepare_source_retry(
    project_id: uuid.UUID,
    source_id: uuid.UUID,
    db: AsyncSession,
) -> Source:
    source = await get_project_source(project_id, source_id, db)
    return await SourceRepository(db).update_status(
        source,
        SourceStatus.PENDING,
        None,
    )


async def mark_source_failed(
    source_id: uuid.UUID,
    error_message: str,
    db: AsyncSession,
) -> Source | None:
    sources = SourceRepository(db)
    source = await sources.get(source_id)
    if source is None:
        return None

    return await sources.update_status(
        source,
        SourceStatus.FAILED,
        error_message,
    )
