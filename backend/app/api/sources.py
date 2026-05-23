import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.sources.service import (
    ProjectNotFoundError,
    SourceNotFoundError,
    UnsupportedSourceTypeError,
    create_uploaded_source,
    get_project_source,
    list_source_fragments,
    list_project_sources,
    mark_source_failed,
)
from app.database import get_db
from app.models.source import Source
from app.models.source_fragment import SourceFragment
from app.schemas.source import SourceFragmentResponse, SourceResponse


router = APIRouter(prefix="/projects/{project_id}/sources", tags=["sources"])


@router.post("", response_model=SourceResponse, status_code=202)
async def upload_source(
    project_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> Source:
    try:
        source = await create_uploaded_source(project_id, file.filename, file.read, db)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnsupportedSourceTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await db.commit()
    try:
        await request.app.state.arq_pool.enqueue_job(
            "ingest_source_job",
            str(source.id),
        )
    except Exception as exc:
        await mark_source_failed(source.id, "Failed to enqueue source ingestion", db)
        await db.commit()
        raise HTTPException(
            status_code=503,
            detail="Failed to enqueue source ingestion",
        ) from exc
    return _source_response(source)


@router.get("", response_model=list[SourceResponse])
async def list_sources(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[SourceResponse]:
    try:
        sources = await list_project_sources(project_id, db)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return [_source_response(source) for source in sources]


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    project_id: uuid.UUID,
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SourceResponse:
    try:
        source = await get_project_source(project_id, source_id, db)
    except (ProjectNotFoundError, SourceNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _source_response(source)


@router.get("/{source_id}/fragments", response_model=list[SourceFragmentResponse])
async def get_source_fragments(
    project_id: uuid.UUID,
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[SourceFragment]:
    try:
        return await list_source_fragments(project_id, source_id, db)
    except (ProjectNotFoundError, SourceNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _source_response(source: Source) -> SourceResponse:
    fragments = list(source.fragments) if "fragments" in source.__dict__ else []
    pages = {
        fragment.page_number
        for fragment in fragments
        if fragment.page_number is not None
    }
    return SourceResponse(
        id=source.id,
        project_id=source.project_id,
        filename=source.filename,
        title=source.title,
        status=source.status,
        fragment_count=len(fragments),
        page_count=len(pages),
        error_message=source.error_message,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )
