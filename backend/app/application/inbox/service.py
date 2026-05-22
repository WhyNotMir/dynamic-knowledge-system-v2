import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.structure.types import ProposalStatus
from app.repositories.projects import ProjectRepository
from app.repositories.structure import StructureRepository


class ProjectNotFoundError(RuntimeError):
    pass


@dataclass(slots=True)
class InboxItem:
    id: uuid.UUID
    project_id: uuid.UUID
    type: str
    status: str
    title: str
    candidate_count: int
    created_at: datetime
    target_id: uuid.UUID


async def list_inbox_items(
    project_id: uuid.UUID,
    db: AsyncSession,
) -> list[InboxItem]:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    proposals = await StructureRepository(db).list_project_proposals(project_id)
    return [
        InboxItem(
            id=proposal.id,
            project_id=proposal.project_id,
            type="structure_proposal",
            status=proposal.status.value,
            title="Review generated article candidates",
            candidate_count=proposal.candidate_count,
            created_at=proposal.created_at,
            target_id=proposal.id,
        )
        for proposal in proposals
        if proposal.status in {ProposalStatus.PENDING, ProposalStatus.READY}
    ]
