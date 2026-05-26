import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.projects import ProjectRepository


class ProjectNotFoundError(RuntimeError):
    pass


async def create_project(
    name: str,
    description: str | None,
    db: AsyncSession,
    settings: dict | None = None,
) -> Project:
    projects = ProjectRepository(db)
    return await projects.create(
        name=name,
        description=description,
        settings=settings,
    )


async def list_projects(db: AsyncSession) -> list[Project]:
    return await ProjectRepository(db).list_all()


async def get_project(project_id: uuid.UUID, db: AsyncSession) -> Project:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")
    return project


async def delete_project(project_id: uuid.UUID, db: AsyncSession) -> None:
    project = await get_project(project_id, db)
    await ProjectRepository(db).delete(project)
