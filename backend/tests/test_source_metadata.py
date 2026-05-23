from app.domain.ingestion.source_metadata import source_title_from_elements
from app.domain.ingestion.types import ElementType, ExtractedElement


def test_source_title_uses_first_top_level_heading():
    title = source_title_from_elements(
        [
            ExtractedElement(
                content="  Attention   Is All You Need  ",
                element_type=ElementType.HEADING,
                position_index=0,
                heading_level=1,
            ),
            ExtractedElement(
                content="Abstract",
                element_type=ElementType.HEADING,
                position_index=1,
                heading_level=1,
            ),
        ]
    )

    assert title == "Attention Is All You Need"


def test_source_title_stops_at_body_heading():
    title = source_title_from_elements(
        [
            ExtractedElement(
                content="Abstract",
                element_type=ElementType.HEADING,
                position_index=0,
                heading_level=1,
            ),
            ExtractedElement(
                content="1 Introduction",
                element_type=ElementType.HEADING,
                position_index=1,
                heading_level=1,
            ),
        ]
    )

    assert title is None


def test_source_title_ignores_author_like_heading():
    title = source_title_from_elements(
        [
            ExtractedElement(
                content="Ashish Vaswani, Noam Shazeer and Niki Parmar",
                element_type=ElementType.HEADING,
                position_index=0,
                heading_level=1,
            ),
            ExtractedElement(
                content="Abstract",
                element_type=ElementType.HEADING,
                position_index=1,
                heading_level=1,
            ),
        ]
    )

    assert title is None
