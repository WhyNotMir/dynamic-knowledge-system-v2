from __future__ import annotations

from dataclasses import dataclass

from app.domain.ingestion.types import ElementType, ExtractedElement


@dataclass(slots=True)
class FragmentData:
    content: str
    element_type: ElementType
    position_index: int
    page_number: int | None = None
    heading_level: int | None = None
    section_path: str | None = None
    meta_json: dict | None = None


def segment_elements(elements: list[ExtractedElement]) -> list[FragmentData]:
    fragments: list[FragmentData] = []

    for element in elements:
        content = _normalize_content(element)
        if not content:
            continue

        fragments.append(
            FragmentData(
                content=content,
                element_type=element.element_type,
                position_index=len(fragments),
                page_number=element.page_number,
                heading_level=element.heading_level,
                section_path=element.section_path,
                meta_json=dict(element.meta_json) if element.meta_json else None,
            )
        )

    return fragments


def _normalize_content(element: ExtractedElement) -> str:
    if element.element_type == ElementType.TABLE:
        lines = [" ".join(line.split()).strip() for line in element.content.splitlines()]
        return "\n".join(line for line in lines if line)

    return " ".join(element.content.split()).strip()
