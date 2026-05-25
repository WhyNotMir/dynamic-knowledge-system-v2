import re

from app.domain.articles.topic_path import article_topic_path, clean_heading_label
from app.domain.ingestion.types import ElementType
from app.models.article import Article, ArticleBlock
from app.schemas.article import ArticleBlockResponse, ArticleDetailResponse, ArticleResponse


def article_response(article: Article) -> ArticleResponse:
    blocks = _loaded_blocks(article)
    sorted_blocks = _sorted_blocks(blocks)
    return ArticleResponse(
        id=article.id,
        project_id=article.project_id,
        candidate_id=article.candidate_id,
        title=article.title,
        topic_path=article_topic_path(
            title=article.title,
            section_paths=[block.section_path for block in sorted_blocks],
        ),
        block_count=len(blocks),
        source_count=len(
            {
                block.fragment.source_id
                for block in blocks
                if "fragment" in block.__dict__ and block.fragment is not None
            }
        ),
        status=article.status,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


def article_detail_response(article: Article) -> ArticleDetailResponse:
    sorted_blocks = _sorted_blocks(_loaded_blocks(article))
    display_flags = _display_flags(sorted_blocks)
    return ArticleDetailResponse(
        **article_response(article).model_dump(),
        blocks=[
            article_block_response(
                block,
                include_in_article=display_flags[index],
                include_in_outline=display_flags[index],
            )
            for index, block in enumerate(sorted_blocks)
        ],
    )


def article_block_response(
    block: ArticleBlock,
    *,
    include_in_article: bool = True,
    include_in_outline: bool = True,
) -> ArticleBlockResponse:
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
        heading_level=response_heading_level(block),
        section_path=block.section_path,
        meta_json=block.meta_json,
        include_in_article=include_in_article,
        include_in_outline=include_in_outline,
        created_at=block.created_at,
    )


def response_heading_level(block: ArticleBlock) -> int | None:
    if block.element_type != ElementType.HEADING:
        return block.heading_level

    numbered_level = _numbered_heading_level(block.content)
    if numbered_level is not None:
        return numbered_level

    return block.heading_level


def _loaded_blocks(article: Article) -> list[ArticleBlock]:
    return list(article.blocks) if "blocks" in article.__dict__ else []


def _sorted_blocks(blocks: list[ArticleBlock]) -> list[ArticleBlock]:
    return sorted(blocks, key=lambda block: block.position_index)


def _display_flags(blocks: list[ArticleBlock]) -> list[bool]:
    flags: list[bool] = []
    for index, block in enumerate(blocks):
        flags.append(not _is_duplicate_unnumbered_heading(block, _next_heading(blocks, index)))
    return flags


def _next_heading(blocks: list[ArticleBlock], index: int) -> ArticleBlock | None:
    for block in blocks[index + 1 :]:
        if block.element_type == ElementType.HEADING:
            return block
    return None


def _is_duplicate_unnumbered_heading(
    block: ArticleBlock,
    next_heading: ArticleBlock | None,
) -> bool:
    if block.element_type != ElementType.HEADING or next_heading is None:
        return False
    if next_heading.element_type != ElementType.HEADING:
        return False
    if _section_number(block.content) is not None:
        return False

    current = clean_heading_label(block.content).lower()
    next_title = clean_heading_label(next_heading.content).lower()
    return bool(current) and next_title.endswith(current)


def _numbered_heading_level(value: str) -> int | None:
    parsed = _section_number(value)
    return min(len(parsed), 6) if parsed is not None else None


def _section_number(value: str) -> tuple[str, ...] | None:
    match = re.match(r"^\s*(\d+(?:\.\d+)*)(?:[.)])?(?=\s+\S)", value)
    if match is None:
        return None
    return tuple(match.group(1).split("."))
