from __future__ import annotations

import uuid

from arq.connections import RedisSettings
from loguru import logger

from app.config import settings
from app.database import AsyncSessionLocal
from app.application.ingestion.service import ingest_source


async def ingest_source_job(ctx, source_id: str) -> None:
    parsed_source_id = uuid.UUID(source_id)

    async with AsyncSessionLocal() as db:
        try:
            source = await ingest_source(parsed_source_id, db)
            await db.commit()

            if source is None:
                logger.warning(f"Source {source_id} not found during worker ingestion")
                return

            logger.info(f"Source {source_id} ingested with status={source.status}")

        except Exception:
            await db.rollback()
            logger.exception(f"Worker failed while ingesting source {source_id}")
            raise


class WorkerSettings:
    functions = [ingest_source_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
