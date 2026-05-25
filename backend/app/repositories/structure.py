import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article_candidate import ArticleCandidate, ArticleCandidateFragment
from app.models.source import Source
from app.models.source_fragment import SourceFragment
from app.models.structure_proposal import StructureProposal
from app.domain.structure.types import CandidateStatus, ProposalStatus


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

    async def get_project_candidate(
        self,
        project_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> ArticleCandidate | None:
        result = await self.db.execute(
            select(ArticleCandidate)
            .join(StructureProposal)
            .where(
                ArticleCandidate.id == candidate_id,
                StructureProposal.project_id == project_id,
            )
            .options(
                selectinload(ArticleCandidate.fragment_links)
                .selectinload(ArticleCandidateFragment.fragment)
            )
        )
        return result.scalar_one_or_none()

    async def update_candidate(
        self,
        candidate: ArticleCandidate,
        *,
        title: str | None = None,
        status: CandidateStatus | None = None,
    ) -> ArticleCandidate:
        if title is not None:
            candidate.title = title
        if status is not None:
            candidate.status = status

        await self.db.flush()
        await self.db.refresh(candidate)
        return candidate

    async def confirm_all_proposal_candidates(
        self,
        project_id: uuid.UUID,
        proposal_id: uuid.UUID,
    ) -> int | None:
        result = await self.db.execute(
            select(StructureProposal)
            .where(
                StructureProposal.id == proposal_id,
                StructureProposal.project_id == project_id,
            )
            .options(selectinload(StructureProposal.candidates))
        )
        proposal = result.scalar_one_or_none()
        if proposal is None:
            return None

        updated_count = 0
        for candidate in proposal.candidates:
            if candidate.status == CandidateStatus.PROPOSED:
                candidate.status = CandidateStatus.CONFIRMED
                updated_count += 1

        await self.db.flush()
        return updated_count

    async def list_project_proposals(
        self,
        project_id: uuid.UUID,
    ) -> list[StructureProposal]:
        result = await self.db.execute(
            select(StructureProposal)
            .where(StructureProposal.project_id == project_id)
            .order_by(StructureProposal.created_at.desc())
            .options(
                selectinload(StructureProposal.candidates)
                .selectinload(ArticleCandidate.fragment_links)
                .selectinload(ArticleCandidateFragment.fragment)
            )
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

    async def delete_candidates_for_source(
        self,
        *,
        project_id: uuid.UUID,
        source_id: uuid.UUID,
    ) -> int:
        candidate_ids = (
            select(ArticleCandidate.id)
            .join(StructureProposal)
            .join(ArticleCandidateFragment)
            .join(SourceFragment, SourceFragment.id == ArticleCandidateFragment.fragment_id)
            .where(
                StructureProposal.project_id == project_id,
                SourceFragment.source_id == source_id,
            )
            .distinct()
        )
        result = await self.db.execute(
            delete(ArticleCandidate).where(ArticleCandidate.id.in_(candidate_ids))
        )
        await self.db.flush()
        await self._refresh_project_proposal_counts(project_id)
        return result.rowcount or 0

    async def _refresh_project_proposal_counts(self, project_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(StructureProposal)
            .where(StructureProposal.project_id == project_id)
            .options(selectinload(StructureProposal.candidates))
        )

        for proposal in result.scalars().all():
            candidate_count = len(proposal.candidates)
            if candidate_count == 0:
                await self.db.delete(proposal)
            else:
                proposal.candidate_count = candidate_count

        await self.db.flush()
