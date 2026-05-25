import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.source import SourceStatus
from app.models.source import Source
from app.models.source_fragment import SourceFragment


class SourceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        *,
        source_id: uuid.UUID,
        project_id: uuid.UUID,
        filename: str,
        storage_path: str,
    ) -> Source:
        source = Source(
            id=source_id,
            project_id=project_id,
            filename=filename,
            storage_path=storage_path,
            status=SourceStatus.PENDING,
        )
        self.db.add(source)
        await self.db.flush()
        await self.db.refresh(source)
        return source

    async def get(self, source_id: uuid.UUID) -> Source | None:
        return await self.db.get(Source, source_id)

    async def get_by_project(
        self,
        project_id: uuid.UUID,
        source_id: uuid.UUID,
    ) -> Source | None:
        result = await self.db.execute(
            select(Source).where(
                Source.id == source_id,
                Source.project_id == project_id,
            )
            .options(selectinload(Source.fragments))
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: uuid.UUID) -> list[Source]:
        result = await self.db.execute(
            select(Source)
            .where(Source.project_id == project_id)
            .options(selectinload(Source.fragments))
            .order_by(Source.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        source: Source,
        status: SourceStatus,
        error_message: str | None,
    ) -> Source:
        source.status = status
        source.error_message = error_message
        await self.db.flush()
        await self.db.refresh(source)
        return source

    async def update_title(self, source: Source, title: str | None) -> Source:
        source.title = title
        await self.db.flush()
        await self.db.refresh(source)
        return source

    async def delete(self, source: Source) -> None:
        await self.db.delete(source)
        await self.db.flush()

    async def replace_fragments(
        self,
        source_id: uuid.UUID,
        fragments: list[SourceFragment],
    ) -> None:
        await self.db.execute(
            delete(SourceFragment).where(SourceFragment.source_id == source_id)
        )
        self.db.add_all(fragments)
        await self.db.flush()

    async def list_fragments(self, source_id: uuid.UUID) -> list[SourceFragment]:
        result = await self.db.execute(
            select(SourceFragment)
            .where(SourceFragment.source_id == source_id)
            .order_by(SourceFragment.position_index)
        )
        return list(result.scalars().all())
