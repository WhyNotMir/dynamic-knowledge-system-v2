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
from app.api.article_presenter import article_detail_response, article_response
from app.database import get_db
from app.schemas.article import (
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
    return [article_response(article) for article in articles]


@router.get("", response_model=list[ArticleResponse])
async def list_project_articles(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ArticleResponse]:
    try:
        articles = await list_articles(project_id, db)
    except QueryProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return [article_response(article) for article in articles]


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

    return article_detail_response(article)
