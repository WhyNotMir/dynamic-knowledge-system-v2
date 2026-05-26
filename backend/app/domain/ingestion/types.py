from __future__ import annotations

import enum
from dataclasses import dataclass


class ElementType(str, enum.Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    CAPTION = "caption"
    QUOTE = "quote"
    CODE_BLOCK = "code_block"
    IMAGE = "image"
    FOOTNOTE = "footnote"
    FORMULA = "formula"
    REFERENCE = "reference"


@dataclass(slots=True)
class ExtractedElement:
    content: str
    element_type: ElementType
    position_index: int
    page_number: int | None = None
    heading_level: int | None = None
    section_path: str | None = None
    meta_json: dict | None = None
