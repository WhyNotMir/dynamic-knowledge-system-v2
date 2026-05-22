import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.projects.service import (
    ProjectNotFoundError,
    create_project as create_project_service,
    delete_project as delete_project_service,
    get_project as get_project_service,
    list_projects as list_projects_service,
)
from app.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> Project:
    project = await create_project_service(payload.name, payload.description, db)
    await db.commit()
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
) -> list[Project]:
    return await list_projects_service(db)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Project:
    try:
        return await get_project_service(project_id, db)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await delete_project_service(project_id, db)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await db.commit()
