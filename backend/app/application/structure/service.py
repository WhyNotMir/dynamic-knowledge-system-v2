import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.structure.candidate_detector import detect_article_candidates
from app.domain.structure.types import CandidateStatus, FragmentForDetection, ProposalStatus
from app.models.article_candidate import ArticleCandidate
from app.models.source_fragment import SourceFragment
from app.models.structure_proposal import StructureProposal
from app.repositories.projects import ProjectRepository
from app.repositories.structure import StructureRepository


class ProjectNotFoundError(RuntimeError):
    pass


class StructureProposalNotFoundError(RuntimeError):
    pass


class ArticleCandidateNotFoundError(RuntimeError):
    pass


async def propose_structure(
    project_id: uuid.UUID,
    db: AsyncSession,
) -> StructureProposal:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    structures = StructureRepository(db)
    fragments = await structures.list_project_fragments(project_id)
    detected_candidates = detect_article_candidates(
        [_fragment_for_detection(fragment) for fragment in fragments]
    )

    proposal = await structures.create_proposal(
        project_id=project_id,
        candidate_count=len(detected_candidates),
    )

    for candidate in detected_candidates:
        await structures.create_candidate(
            proposal_id=proposal.id,
            title=candidate.title,
            source_section_path=candidate.source_section_path,
            suggested_order=candidate.suggested_order,
            fragment_ids=candidate.fragment_ids,
        )

    await structures.update_proposal_status(proposal, ProposalStatus.READY)

    loaded = await structures.get_project_proposal(project_id, proposal.id)
    if loaded is None:
        raise StructureProposalNotFoundError("Structure proposal not found")
    return loaded


async def list_structure_proposals(
    project_id: uuid.UUID,
    db: AsyncSession,
) -> list[StructureProposal]:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    return await StructureRepository(db).list_project_proposals(project_id)


async def get_structure_proposal(
    project_id: uuid.UUID,
    proposal_id: uuid.UUID,
    db: AsyncSession,
) -> StructureProposal:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    proposal = await StructureRepository(db).get_project_proposal(
        project_id,
        proposal_id,
    )
    if proposal is None:
        raise StructureProposalNotFoundError("Structure proposal not found")
    return proposal


async def update_candidate(
    project_id: uuid.UUID,
    candidate_id: uuid.UUID,
    db: AsyncSession,
    *,
    title: str | None = None,
    status: CandidateStatus | None = None,
) -> ArticleCandidate:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    structures = StructureRepository(db)
    candidate = await structures.get_project_candidate(project_id, candidate_id)
    if candidate is None:
        raise ArticleCandidateNotFoundError("Article candidate not found")

    return await structures.update_candidate(
        candidate,
        title=title,
        status=status,
    )


async def confirm_all_candidates(
    project_id: uuid.UUID,
    proposal_id: uuid.UUID,
    db: AsyncSession,
) -> int:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    updated_count = await StructureRepository(db).confirm_all_proposal_candidates(
        project_id,
        proposal_id,
    )
    if updated_count is None:
        raise StructureProposalNotFoundError("Structure proposal not found")

    return updated_count


def _fragment_for_detection(fragment: SourceFragment) -> FragmentForDetection:
    return FragmentForDetection(
        id=fragment.id,
        source_id=fragment.source_id,
        content=fragment.content,
        element_type=fragment.element_type,
        position_index=fragment.position_index,
        heading_level=fragment.heading_level,
        section_path=fragment.section_path,
    )
