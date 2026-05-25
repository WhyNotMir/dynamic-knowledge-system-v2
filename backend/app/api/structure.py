import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.structure.service import (
    ArticleCandidateNotFoundError,
    ProjectNotFoundError,
    StructureProposalNotFoundError,
    confirm_all_candidates,
    get_structure_proposal,
    list_structure_proposals,
    propose_structure,
    update_candidate,
)
from app.database import get_db
from app.models.article_candidate import ArticleCandidate
from app.models.structure_proposal import StructureProposal
from app.domain.ingestion.types import ElementType
from app.schemas.structure import (
    ArticleCandidateDetailResponse,
    ArticleCandidateFragmentResponse,
    ArticleCandidateResponse,
    ConfirmAllResponse,
    StructureProposalDetailResponse,
    StructureProposalResponse,
    UpdateCandidateRequest,
)


router = APIRouter(prefix="/projects/{project_id}/structure", tags=["structure"])


@router.post("/propose", response_model=StructureProposalDetailResponse, status_code=201)
async def create_structure_proposal(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StructureProposalDetailResponse:
    try:
        proposal = await propose_structure(project_id, db)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await db.commit()
    return _proposal_detail_response(proposal)


@router.get("/proposals", response_model=list[StructureProposalResponse])
async def list_proposals(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[StructureProposalResponse]:
    try:
        proposals = await list_structure_proposals(project_id, db)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return [
        _proposal_response(proposal)
        for proposal in proposals
    ]


@router.get(
    "/proposals/{proposal_id}",
    response_model=StructureProposalDetailResponse,
)
async def get_proposal(
    project_id: uuid.UUID,
    proposal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StructureProposalDetailResponse:
    try:
        proposal = await get_structure_proposal(project_id, proposal_id, db)
    except (ProjectNotFoundError, StructureProposalNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _proposal_detail_response(proposal)


@router.patch(
    "/candidates/{candidate_id}",
    response_model=ArticleCandidateDetailResponse,
)
async def patch_candidate(
    project_id: uuid.UUID,
    candidate_id: uuid.UUID,
    payload: UpdateCandidateRequest,
    db: AsyncSession = Depends(get_db),
) -> ArticleCandidateDetailResponse:
    try:
        candidate = await update_candidate(
            project_id,
            candidate_id,
            db,
            title=payload.title,
            status=payload.status,
        )
    except (ProjectNotFoundError, ArticleCandidateNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await db.commit()
    return _candidate_detail_response(candidate)


@router.post(
    "/proposals/{proposal_id}/confirm-all",
    response_model=ConfirmAllResponse,
)
async def confirm_all_proposal_candidates(
    project_id: uuid.UUID,
    proposal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ConfirmAllResponse:
    try:
        updated_count = await confirm_all_candidates(project_id, proposal_id, db)
    except (ProjectNotFoundError, StructureProposalNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await db.commit()
    return ConfirmAllResponse(updated_count=updated_count)


def _proposal_response(proposal: StructureProposal) -> StructureProposalResponse:
    return StructureProposalResponse(
        id=proposal.id,
        project_id=proposal.project_id,
        status=proposal.status,
        candidate_count=proposal.candidate_count,
        created_at=proposal.created_at,
        updated_at=proposal.updated_at,
        candidates=[
            _candidate_response(candidate)
            for candidate in sorted(
                proposal.candidates,
                key=lambda candidate: candidate.suggested_order,
            )
        ],
    )


def _proposal_detail_response(
    proposal: StructureProposal,
) -> StructureProposalDetailResponse:
    return StructureProposalDetailResponse(
        id=proposal.id,
        project_id=proposal.project_id,
        status=proposal.status,
        candidate_count=proposal.candidate_count,
        created_at=proposal.created_at,
        updated_at=proposal.updated_at,
        candidates=[
            _candidate_detail_response(candidate)
            for candidate in sorted(
                proposal.candidates,
                key=lambda candidate: candidate.suggested_order,
            )
        ],
    )


def _candidate_response(candidate: ArticleCandidate) -> ArticleCandidateResponse:
    return ArticleCandidateResponse(
        id=candidate.id,
        proposal_id=candidate.proposal_id,
        title=candidate.title,
        source_section_path=candidate.source_section_path,
        status=candidate.status,
        suggested_order=candidate.suggested_order,
        created_at=candidate.created_at,
        internal_headings=_internal_headings(candidate),
        fragments=_candidate_fragments(candidate),
    )


def _candidate_detail_response(
    candidate: ArticleCandidate,
) -> ArticleCandidateDetailResponse:
    return ArticleCandidateDetailResponse(
        **_candidate_response(candidate).model_dump()
    )


def _candidate_fragments(
    candidate: ArticleCandidate,
) -> list[ArticleCandidateFragmentResponse]:
    return [
        ArticleCandidateFragmentResponse(
            fragment_id=link.fragment_id,
            position_index=link.position_index,
            content=link.fragment.content,
        )
        for link in sorted(
            candidate.fragment_links,
            key=lambda link: link.position_index,
        )
    ]


def _internal_headings(candidate: ArticleCandidate) -> list[str]:
    headings: list[str] = []
    seen: set[str] = set()
    for link in sorted(candidate.fragment_links, key=lambda link: link.position_index):
        fragment = link.fragment
        if fragment is None or fragment.element_type != ElementType.HEADING:
            continue
        if link.position_index == 0 and _same_heading(fragment.content, candidate.title):
            continue
        text = " ".join(fragment.content.split()).strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        headings.append(text)
    return headings


def _same_heading(left: str, right: str) -> bool:
    return _heading_key(left) == _heading_key(right)


def _heading_key(value: str) -> str:
    return " ".join(value.split()).casefold()
