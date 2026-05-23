import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article, ArticleBlock
from app.models.article_candidate import ArticleCandidate, ArticleCandidateFragment
from app.models.source_fragment import SourceFragment


class ArticleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_candidate(self, candidate_id: uuid.UUID) -> Article | None:
        result = await self.db.execute(
            select(Article).where(Article.candidate_id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def create_from_candidate(
        self,
        *,
        project_id: uuid.UUID,
        candidate: ArticleCandidate,
    ) -> Article:
        article = Article(
            project_id=project_id,
            candidate_id=candidate.id,
            title=candidate.title,
        )
        self.db.add(article)
        await self.db.flush()

        self.db.add_all(
            [
                ArticleBlock(
                    article_id=article.id,
                    fragment_id=link.fragment.id,
                    content=link.fragment.content,
                    element_type=link.fragment.element_type,
                    position_index=link.position_index,
                    page_number=link.fragment.page_number,
                    heading_level=link.fragment.heading_level,
                    section_path=link.fragment.section_path,
                    meta_json=link.fragment.meta_json,
                )
                for link in sorted(
                    candidate.fragment_links,
                    key=lambda link: link.position_index,
                )
            ]
        )
        await self.db.flush()
        await self.db.refresh(article)
        return article

    async def list_by_project(self, project_id: uuid.UUID) -> list[Article]:
        result = await self.db.execute(
            select(Article)
            .where(Article.project_id == project_id)
            .order_by(Article.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_project(
        self,
        project_id: uuid.UUID,
        article_id: uuid.UUID,
    ) -> Article | None:
        result = await self.db.execute(
            select(Article)
            .where(
                Article.id == article_id,
                Article.project_id == project_id,
            )
            .options(
                selectinload(Article.blocks)
                .selectinload(ArticleBlock.fragment)
                .selectinload(SourceFragment.source)
            )
        )
        return result.scalar_one_or_none()

    async def list_candidates_for_proposal(
        self,
        proposal_id: uuid.UUID,
    ) -> list[ArticleCandidate]:
        result = await self.db.execute(
            select(ArticleCandidate)
            .where(ArticleCandidate.proposal_id == proposal_id)
            .options(
                selectinload(ArticleCandidate.fragment_links)
                .selectinload(ArticleCandidateFragment.fragment)
            )
            .order_by(ArticleCandidate.suggested_order)
        )
        return list(result.scalars().all())
