from __future__ import annotations

import re

from app.domain.ingestion.document_markers import SOURCE_TITLE_STOP_HEADINGS
from app.domain.ingestion.types import ElementType, ExtractedElement


def source_title_from_elements(elements: list[ExtractedElement]) -> str | None:
    for element in elements:
        if element.element_type != ElementType.HEADING:
            continue
        if element.heading_level != 1:
            continue

        title = " ".join(element.content.split()).strip()
        if not title:
            continue
        if title.casefold() in SOURCE_TITLE_STOP_HEADINGS:
            return None
        if _looks_like_author_heading(title):
            continue
        return title

    return None


def _looks_like_author_heading(value: str) -> bool:
    text = " ".join(value.split()).strip()
    if not text:
        return False
    if len(text) > 180:
        return False
    if not any(separator in text.casefold() for separator in (" and ", ",", " & ")):
        return False

    words = [word for word in re.split(r"\s+", text) if word]
    capitalized = sum(1 for word in words if word[:1].isupper())
    return capitalized >= 3
