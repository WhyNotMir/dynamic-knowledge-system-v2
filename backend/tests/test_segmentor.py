from app.domain.ingestion.segmentor import segment_elements
from app.domain.ingestion.types import ElementType, ExtractedElement


def test_segmentor_skips_empty_elements_and_reindexes_positions():
    fragments = segment_elements(
        [
            ExtractedElement(
                content="   ",
                element_type=ElementType.PARAGRAPH,
                position_index=10,
            ),
            ExtractedElement(
                content="  First   paragraph.  ",
                element_type=ElementType.PARAGRAPH,
                position_index=11,
            ),
            ExtractedElement(
                content="\nSecond\tparagraph.\n",
                element_type=ElementType.PARAGRAPH,
                position_index=12,
            ),
        ]
    )

    assert [fragment.content for fragment in fragments] == [
        "First paragraph.",
        "Second paragraph.",
    ]
    assert [fragment.position_index for fragment in fragments] == [0, 1]


def test_segmentor_preserves_table_line_structure():
    fragments = segment_elements(
        [
            ExtractedElement(
                content=" Col A    Col B \n\n  1      2  \n  3      4 ",
                element_type=ElementType.TABLE,
                position_index=0,
                page_number=2,
                section_path="Results",
            )
        ]
    )

    assert len(fragments) == 1
    assert fragments[0].content == "Col A Col B\n1 2\n3 4"
    assert fragments[0].element_type == ElementType.TABLE
    assert fragments[0].page_number == 2
    assert fragments[0].section_path == "Results"


def test_segmentor_preserves_element_type_heading_and_metadata():
    fragments = segment_elements(
        [
            ExtractedElement(
                content="  1   Introduction  ",
                element_type=ElementType.HEADING,
                position_index=0,
                page_number=1,
                heading_level=1,
                section_path="1 Introduction",
                meta_json={"source_label": "section_header"},
            )
        ]
    )

    assert len(fragments) == 1
    assert fragments[0].content == "1 Introduction"
    assert fragments[0].element_type == ElementType.HEADING
    assert fragments[0].heading_level == 1
    assert fragments[0].section_path == "1 Introduction"
    assert fragments[0].meta_json == {"source_label": "section_header"}


def test_segmentor_does_not_make_semantic_or_article_decisions():
    fragments = segment_elements(
        [
            ExtractedElement(
                content="Abstract",
                element_type=ElementType.HEADING,
                position_index=0,
                heading_level=1,
            ),
            ExtractedElement(
                content="This paper introduces a model.",
                element_type=ElementType.PARAGRAPH,
                position_index=1,
                section_path="Abstract",
            ),
        ]
    )

    assert len(fragments) == 2
    assert all(not hasattr(fragment, "title") for fragment in fragments)
    assert all(not hasattr(fragment, "candidate_id") for fragment in fragments)
