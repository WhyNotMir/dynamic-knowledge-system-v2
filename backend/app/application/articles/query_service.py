import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.repositories.articles import ArticleRepository
from app.repositories.projects import ProjectRepository


class ArticleNotFoundError(RuntimeError):
    pass


class ProjectNotFoundError(RuntimeError):
    pass


async def list_articles(
    project_id: uuid.UUID,
    db: AsyncSession,
) -> list[Article]:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    return await ArticleRepository(db).list_by_project(project_id)


async def get_article(
    project_id: uuid.UUID,
    article_id: uuid.UUID,
    db: AsyncSession,
) -> Article:
    project = await ProjectRepository(db).get(project_id)
    if project is None:
        raise ProjectNotFoundError("Project not found")

    article = await ArticleRepository(db).get_by_project(project_id, article_id)
    if article is None:
        raise ArticleNotFoundError("Article not found")

    return article
