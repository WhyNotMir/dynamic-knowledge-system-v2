from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from app.domain.ingestion.document_markers import REFERENCE_HEADINGS
from app.domain.ingestion.types import ElementType, ExtractedElement


CAPTION_RE = re.compile(
    r"^(?i:(?:figure|fig\.?|table))\s+"
    r"(?:\d+(?:\.\d+)*|[IVXLC]+|[A-Z])[.:)\-–]?\s+",
)


def extract_pdf(file_path: str | Path) -> list[ExtractedElement]:
    path = Path(file_path)
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported")
    result = _converter().convert(path)
    return _normalise_docling_document(result.document)

@lru_cache(maxsize=1)
def _converter() -> DocumentConverter:
    pdf_options = PdfPipelineOptions()
    pdf_options.do_ocr = False
    pdf_options.do_table_structure = True

    return DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options),
        },
    )

def _normalise_docling_document(document: Any) -> list[ExtractedElement]:
    elements: list[ExtractedElement] = []
    heading_stack: list[tuple[int, str]] = []
    in_references = False

    for item, raw_level in document.iterate_items():
        label = _label_value(item)
        text = _normalise_text(getattr(item, "text", "") or "")

        if label == "table":
            content = text or "Table"
            element_type = ElementType.TABLE
            heading_level = None
            meta_json = {"source_label": label}
        else:
            if not text:
                continue

            element_type, heading_level = _classify_text(
                label=label,
                text=text,
                raw_level=raw_level,
                in_references=in_references,
            )
            meta_json = {"source_label": label}

            if element_type == ElementType.HEADING:
                if text.strip().lower() in REFERENCE_HEADINGS:
                    in_references = True

                level = heading_level or 1
                heading_stack = [
                    (existing_level, title)
                    for existing_level, title in heading_stack
                    if existing_level < level
                ]
                heading_stack.append((level, text))

            content = text

        elements.append(
            ExtractedElement(
                content=content,
                element_type=element_type,
                position_index=len(elements),
                page_number=_page_number(item),
                heading_level=heading_level,
                section_path=_section_path(heading_stack),
                meta_json=meta_json,
            )
        )

    return elements


def _classify_text(
    *,
    label: str,
    text: str,
    raw_level: int | None,
    in_references: bool,
) -> tuple[ElementType, int | None]:
    normalized = text.strip().lower()

    if normalized in REFERENCE_HEADINGS:
        return ElementType.HEADING, 1

    if in_references:
        return ElementType.REFERENCE, None

    if label in {"section_header", "title"}:
        return ElementType.HEADING, _heading_level(raw_level)

    if label == "list_item":
        return ElementType.LIST_ITEM, None

    if label in {"formula", "equation"}:
        return ElementType.FORMULA, None

    if _looks_like_caption(text):
        return ElementType.CAPTION, None

    return ElementType.PARAGRAPH, None


def _label_value(item: Any) -> str:
    label = getattr(item, "label", "")
    value = getattr(label, "value", label)
    return str(value).lower()


def _normalise_text(value: str) -> str:
    return " ".join(value.split()).strip()


def _heading_level(raw_level: int | None) -> int:
    if raw_level is None:
        return 1

    try:
        return max(1, min(int(raw_level), 6))
    except (TypeError, ValueError):
        return 1


def _page_number(item: Any) -> int | None:
    prov = getattr(item, "prov", None)
    if not prov:
        return None

    first = prov[0] if isinstance(prov, list) else prov
    page_no = getattr(first, "page_no", None)

    try:
        return int(page_no) if page_no is not None else None
    except (TypeError, ValueError):
        return None


def _section_path(heading_stack: list[tuple[int, str]]) -> str | None:
    if not heading_stack:
        return None

    return " > ".join(title for _, title in heading_stack)


def _looks_like_caption(text: str) -> bool:
    return bool(CAPTION_RE.match(text.strip()))
