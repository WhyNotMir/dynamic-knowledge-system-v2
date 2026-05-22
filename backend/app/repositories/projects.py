import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        *,
        name: str,
        description: str | None,
    ) -> Project:
        project = Project(name=name, description=description)
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def get(self, project_id: uuid.UUID) -> Project | None:
        return await self.db.get(Project, project_id)

    async def list_all(self) -> list[Project]:
        result = await self.db.execute(
            select(Project).order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, project: Project) -> None:
        await self.db.delete(project)
