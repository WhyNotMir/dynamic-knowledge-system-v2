import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article_candidate import ArticleCandidate, ArticleCandidateFragment
from app.models.source import Source
from app.models.source_fragment import SourceFragment
from app.models.structure_proposal import StructureProposal
from app.domain.structure.types import ProposalStatus


class StructureRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_project_fragments(self, project_id: uuid.UUID) -> list[SourceFragment]:
        result = await self.db.execute(
            select(SourceFragment)
            .join(Source)
            .where(Source.project_id == project_id)
            .order_by(Source.created_at, Source.filename, SourceFragment.position_index)
        )
        return list(result.scalars().all())

    async def create_proposal(
        self,
        *,
        project_id: uuid.UUID,
        candidate_count: int,
    ) -> StructureProposal:
        proposal = StructureProposal(
            project_id=project_id,
            candidate_count=candidate_count,
        )
        self.db.add(proposal)
        await self.db.flush()
        await self.db.refresh(proposal)
        return proposal

    async def create_candidate(
        self,
        *,
        proposal_id: uuid.UUID,
        title: str,
        source_section_path: str,
        suggested_order: int,
        fragment_ids: list[uuid.UUID],
    ) -> ArticleCandidate:
        candidate = ArticleCandidate(
            proposal_id=proposal_id,
            title=title,
            source_section_path=source_section_path,
            suggested_order=suggested_order,
        )
        self.db.add(candidate)
        await self.db.flush()

        self.db.add_all(
            [
                ArticleCandidateFragment(
                    candidate_id=candidate.id,
                    fragment_id=fragment_id,
                    position_index=position_index,
                )
                for position_index, fragment_id in enumerate(fragment_ids)
            ]
        )
        await self.db.flush()
        await self.db.refresh(candidate)
        return candidate

    async def update_proposal_status(
        self,
        proposal: StructureProposal,
        status: ProposalStatus,
    ) -> StructureProposal:
        proposal.status = status
        await self.db.flush()
        await self.db.refresh(proposal)
        return proposal

    async def list_project_proposals(
        self,
        project_id: uuid.UUID,
    ) -> list[StructureProposal]:
        result = await self.db.execute(
            select(StructureProposal)
            .where(StructureProposal.project_id == project_id)
            .order_by(StructureProposal.created_at.desc())
            .options(selectinload(StructureProposal.candidates))
        )
        return list(result.scalars().all())

    async def get_project_proposal(
        self,
        project_id: uuid.UUID,
        proposal_id: uuid.UUID,
    ) -> StructureProposal | None:
        result = await self.db.execute(
            select(StructureProposal)
            .where(
                StructureProposal.id == proposal_id,
                StructureProposal.project_id == project_id,
            )
            .options(
                selectinload(StructureProposal.candidates)
                .selectinload(ArticleCandidate.fragment_links)
                .selectinload(ArticleCandidateFragment.fragment)
            )
        )
        return result.scalar_one_or_none()
