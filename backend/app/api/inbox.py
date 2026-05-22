import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.inbox.service import (
    InboxItem,
    ProjectNotFoundError,
    list_inbox_items,
)
from app.database import get_db
from app.schemas.inbox import InboxItemResponse


router = APIRouter(prefix="/projects/{project_id}/inbox", tags=["inbox"])


@router.get("", response_model=list[InboxItemResponse])
async def get_inbox(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[InboxItemResponse]:
    try:
        items = await list_inbox_items(project_id, db)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return [_inbox_item_response(item) for item in items]


def _inbox_item_response(item: InboxItem) -> InboxItemResponse:
    return InboxItemResponse(
        id=item.id,
        project_id=item.project_id,
        type=item.type,
        status=item.status,
        title=item.title,
        candidate_count=item.candidate_count,
        created_at=item.created_at,
        target_id=item.target_id,
    )
