import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.structure.types import CandidateStatus, ProposalStatus
from app.models.article import Article
from app.repositories.articles import ArticleRepository
from app.repositories.projects import ProjectRepository
from app.repositories.structure import StructureRepository


class ProjectNotFoundError(RuntimeError):
    pass


class StructureProposalNotFoundError(RuntimeError):
    pass


async def build_articles(
    project_id: uuid.UUID,
    proposal_id: uuid.UUID,
    db: AsyncSession,
) -> list[Article]:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    structures = StructureRepository(db)
    proposal = await structures.get_project_proposal(project_id, proposal_id)
    if proposal is None:
        raise StructureProposalNotFoundError("Structure proposal not found")

    articles = ArticleRepository(db)
    built_articles: list[Article] = []
    candidates = await articles.list_candidates_for_proposal(proposal_id)

    for candidate in candidates:
        if candidate.status != CandidateStatus.CONFIRMED:
            continue

        existing = await articles.get_by_candidate(candidate.id)
        if existing is not None:
            built_articles.append(existing)
            continue

        built_articles.append(
            await articles.create_from_candidate(
                project_id=project_id,
                candidate=candidate,
            )
        )

    await structures.update_proposal_status(proposal, ProposalStatus.REVIEWED)
    return built_articles
