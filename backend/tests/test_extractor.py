import pytest

from types import SimpleNamespace

from app.domain.ingestion.extractor import extract_pdf, _normalise_docling_document
from app.domain.ingestion.types import ElementType


def test_extract_pdf_rejects_non_pdf_suffix(tmp_path):
    text_path = tmp_path / "source.txt"
    text_path.write_text("not a pdf")

    with pytest.raises(ValueError, match="Only PDF files are supported"):
        extract_pdf(text_path)


def test_normalise_docling_document_preserves_heading_stack_and_pages():
    document = FakeDocument(
        [
            item("title", "Paper Title", page_no=1),
            item("section_header", "1 Introduction", level=1, page_no=2),
            item("text", "Body paragraph.", page_no=2),
            item("section_header", "1.1 Details", level=2, page_no=3),
            item("text", "Nested paragraph.", page_no=3),
        ]
    )

    elements = _normalise_docling_document(document)

    assert [element.content for element in elements] == [
        "Paper Title",
        "1 Introduction",
        "Body paragraph.",
        "1.1 Details",
        "Nested paragraph.",
    ]
    assert elements[0].element_type == ElementType.HEADING
    assert elements[0].section_path == "Paper Title"
    assert elements[2].element_type == ElementType.PARAGRAPH
    assert elements[2].section_path == "1 Introduction"
    assert elements[4].section_path == "1 Introduction > 1.1 Details"
    assert elements[4].page_number == 3


def test_normalise_docling_document_classifies_references():
    document = FakeDocument(
        [
            item("section_header", "References", level=1, page_no=9),
            item("text", "[1] A cited work.", page_no=9),
            item("text", "2. Another cited work.", page_no=9),
        ]
    )

    elements = _normalise_docling_document(document)

    assert elements[0].element_type == ElementType.HEADING
    assert [element.element_type for element in elements[1:]] == [
        ElementType.REFERENCE,
        ElementType.REFERENCE,
    ]
    assert all(element.section_path == "References" for element in elements)


def test_normalise_docling_document_classifies_captions_conservatively():
    document = FakeDocument(
        [
            item("text", "Figure 1: Model architecture.", page_no=4),
            item("text", "Fig. 2 Encoder stack.", page_no=5),
            item("text", "Table of contents", page_no=1),
        ]
    )

    elements = _normalise_docling_document(document)

    assert elements[0].element_type == ElementType.CAPTION
    assert elements[1].element_type == ElementType.CAPTION
    assert elements[2].element_type == ElementType.PARAGRAPH


class FakeDocument:
    def __init__(self, entries):
        self.entries = entries

    def iterate_items(self):
        return iter(self.entries)


def item(label: str, text: str, *, level: int | None = None, page_no: int | None = None):
    return (
        SimpleNamespace(
            label=SimpleNamespace(value=label),
            text=text,
            prov=[SimpleNamespace(page_no=page_no)] if page_no is not None else [],
        ),
        level,
    )
