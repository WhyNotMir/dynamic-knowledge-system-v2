from __future__ import annotations

import uuid

from app.domain.ingestion.types import ElementType
from app.domain.structure.types import DetectedCandidate, FragmentForDetection


def detect_article_candidates(
    fragments: list[FragmentForDetection],
) -> list[DetectedCandidate]:
    candidates: list[DetectedCandidate] = []
    current_title: str | None = None
    current_group_key: str | None = None
    current_source_id: uuid.UUID | None = None
    current_fragment_ids: list[uuid.UUID] = []

    for fragment in fragments:
        if not fragment.content.strip():
            continue

        group_key = _top_level_section(fragment)
        source_changed = (
            current_source_id is not None
            and fragment.source_id != current_source_id
        )
        section_changed = (
            current_group_key is not None
            and group_key is not None
            and group_key != current_group_key
        )
        starts_new_group = (
            source_changed
            or section_changed
            or _starts_top_level_section(fragment)
        )

        if starts_new_group:
            if _is_meaningful_group(current_fragment_ids):
                candidates.append(
                    DetectedCandidate(
                        title=current_title or "Untitled",
                        source_section_path=current_group_key or current_title or "Untitled",
                        suggested_order=len(candidates),
                        fragment_ids=current_fragment_ids,
                    )
                )

            current_title = _candidate_title(fragment)
            current_group_key = group_key or current_title
            current_source_id = fragment.source_id
            current_fragment_ids = [fragment.id]
            continue

        if current_fragment_ids:
            current_fragment_ids.append(fragment.id)
        else:
            current_title = _candidate_title(fragment)
            current_group_key = group_key or current_title
            current_source_id = fragment.source_id
            current_fragment_ids = [fragment.id]

    if _is_meaningful_group(current_fragment_ids):
        candidates.append(
            DetectedCandidate(
                title=current_title or "Untitled",
                source_section_path=current_group_key or current_title or "Untitled",
                suggested_order=len(candidates),
                fragment_ids=current_fragment_ids,
            )
        )

    return candidates


def _starts_top_level_section(fragment: FragmentForDetection) -> bool:
    return (
        fragment.element_type == ElementType.HEADING
        and (fragment.heading_level is None or fragment.heading_level <= 1)
    )


def _candidate_title(fragment: FragmentForDetection) -> str:
    section = _top_level_section(fragment)
    if section:
        return section
    return fragment.content.strip() or "Untitled"


def _top_level_section(fragment: FragmentForDetection) -> str | None:
    if not fragment.section_path:
        return None
    return fragment.section_path.split(" > ", 1)[0].strip() or None


def _is_meaningful_group(fragment_ids: list[uuid.UUID]) -> bool:
    return bool(fragment_ids)
