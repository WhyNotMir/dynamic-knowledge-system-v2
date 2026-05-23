import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.articles.build_service import (
    ProjectNotFoundError as BuildProjectNotFoundError,
)
from app.application.articles.build_service import (
    StructureProposalNotFoundError,
    build_articles,
)
from app.application.articles.query_service import (
    ArticleNotFoundError,
    ProjectNotFoundError as QueryProjectNotFoundError,
    get_article,
    list_articles,
)
from app.database import get_db
from app.models.article import Article, ArticleBlock
from app.schemas.article import (
    ArticleBlockResponse,
    ArticleDetailResponse,
    ArticleResponse,
    BuildArticlesRequest,
)


router = APIRouter(prefix="/projects/{project_id}/articles", tags=["articles"])


@router.post("/build", response_model=list[ArticleResponse], status_code=201)
async def build_project_articles(
    project_id: uuid.UUID,
    payload: BuildArticlesRequest,
    db: AsyncSession = Depends(get_db),
) -> list[ArticleResponse]:
    try:
        articles = await build_articles(project_id, payload.proposal_id, db)
    except (BuildProjectNotFoundError, StructureProposalNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await db.commit()
    return [_article_response(article) for article in articles]


@router.get("", response_model=list[ArticleResponse])
async def list_project_articles(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ArticleResponse]:
    try:
        articles = await list_articles(project_id, db)
    except QueryProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return [_article_response(article) for article in articles]


@router.get("/{article_id}", response_model=ArticleDetailResponse)
async def get_project_article(
    project_id: uuid.UUID,
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ArticleDetailResponse:
    try:
        article = await get_article(project_id, article_id, db)
    except (QueryProjectNotFoundError, ArticleNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _article_detail_response(article)


def _article_response(article: Article) -> ArticleResponse:
    return ArticleResponse(
        id=article.id,
        project_id=article.project_id,
        candidate_id=article.candidate_id,
        title=article.title,
        status=article.status,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


def _article_detail_response(article: Article) -> ArticleDetailResponse:
    return ArticleDetailResponse(
        **_article_response(article).model_dump(),
        blocks=[
            _article_block_response(block)
            for block in sorted(article.blocks, key=lambda block: block.position_index)
        ],
    )


def _article_block_response(block: ArticleBlock) -> ArticleBlockResponse:
    return ArticleBlockResponse(
        id=block.id,
        article_id=block.article_id,
        fragment_id=block.fragment_id,
        source_title=block.fragment.source.title,
        source_filename=block.fragment.source.filename,
        content=block.content,
        element_type=block.element_type,
        position_index=block.position_index,
        page_number=block.page_number,
        heading_level=block.heading_level,
        section_path=block.section_path,
        meta_json=block.meta_json,
        created_at=block.created_at,
    )
