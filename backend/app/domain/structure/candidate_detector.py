from __future__ import annotations

import re
import uuid

from app.domain.ingestion.types import ElementType
from app.domain.ingestion.document_markers import REFERENCE_HEADINGS
from app.domain.structure.types import DetectedCandidate, FragmentForDetection


def detect_article_candidates(
    fragments: list[FragmentForDetection],
) -> list[DetectedCandidate]:
    candidates: list[DetectedCandidate] = []
    current_title: str | None = None
    current_group_key: str | None = None
    current_source_id: uuid.UUID | None = None
    current_numbered_parent: str | None = None
    current_fragment_ids: list[uuid.UUID] = []

    for fragment in fragments:
        if not fragment.content.strip():
            continue

        source_changed = (
            current_source_id is not None
            and fragment.source_id != current_source_id
        )
        if source_changed:
            if _is_meaningful_group(current_fragment_ids):
                candidates.append(
                    DetectedCandidate(
                        title=current_title or "Untitled",
                        source_section_path=current_group_key or current_title or "Untitled",
                        suggested_order=len(candidates),
                        fragment_ids=current_fragment_ids,
                    )
                )

            current_title = None
            current_group_key = None
            current_source_id = fragment.source_id
            current_numbered_parent = None
            current_fragment_ids = []

        if not current_fragment_ids and not _can_start_candidate(fragment):
            current_source_id = fragment.source_id
            continue

        group_key = _group_key(
            fragment,
            current_group_key,
            current_numbered_parent,
        )
        if (
            current_numbered_parent is not None
            and current_group_key is not None
            and fragment.element_type != ElementType.HEADING
            and _section_number(_top_level_section(fragment)) is None
        ):
            group_key = current_group_key
        section_changed = (
            current_group_key is not None
            and group_key is not None
            and group_key != current_group_key
        )
        heading_without_group = (
            current_group_key is not None
            and group_key is None
            and _starts_top_level_section(fragment)
        )
        starts_new_group = (
            section_changed
            or heading_without_group
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

            current_title = _candidate_title(fragment, group_key)
            current_group_key = group_key or current_title
            current_source_id = fragment.source_id
            current_numbered_parent = _major_section_number(current_group_key)
            current_fragment_ids = [fragment.id]
            continue

        if current_fragment_ids:
            current_fragment_ids.append(fragment.id)
            current_numbered_parent = (
                _major_section_number(_heading_text(fragment))
                or current_numbered_parent
            )
        else:
            current_title = _candidate_title(fragment, group_key)
            current_group_key = group_key or current_title
            current_source_id = fragment.source_id
            current_numbered_parent = _major_section_number(current_group_key)
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


def _can_start_candidate(fragment: FragmentForDetection) -> bool:
    return _top_level_section(fragment) is not None or _heading_text(fragment) is not None


def _starts_top_level_section(fragment: FragmentForDetection) -> bool:
    return (
        fragment.element_type == ElementType.HEADING
        and (fragment.heading_level is None or fragment.heading_level <= 1)
        and not _is_numbered_subsection(_heading_text(fragment))
    )


def _candidate_title(fragment: FragmentForDetection, group_key: str | None) -> str:
    section = group_key or _top_level_section(fragment)
    if section:
        return section
    return fragment.content.strip() or "Untitled"


def _group_key(
    fragment: FragmentForDetection,
    current_group_key: str | None,
    current_numbered_parent: str | None,
) -> str | None:
    heading_text = _heading_text(fragment)
    if heading_text and _same_numbered_parent(heading_text, current_group_key):
        return current_group_key
    if (
        heading_text
        and current_numbered_parent is not None
        and not _is_document_terminal_heading(heading_text)
        and not _section_number(heading_text)
    ):
        return current_group_key

    top_section = _top_level_section(fragment)
    if top_section:
        if _same_numbered_parent(top_section, current_group_key):
            return current_group_key
        return top_section

    if heading_text:
        if not _is_numbered_subsection(heading_text):
            return heading_text

    return None


def _top_level_section(fragment: FragmentForDetection) -> str | None:
    if not fragment.section_path:
        return None
    return fragment.section_path.split(" > ", 1)[0].strip() or None


def _is_meaningful_group(fragment_ids: list[uuid.UUID]) -> bool:
    return bool(fragment_ids)


def _heading_text(fragment: FragmentForDetection) -> str | None:
    if fragment.element_type != ElementType.HEADING:
        return None
    text = fragment.content.strip()
    return text or None


def _same_numbered_parent(
    section: str,
    current_group_key: str | None,
) -> bool:
    if current_group_key is None or not _is_numbered_subsection(section):
        return False

    section_major = _major_section_number(section)
    current_major = _major_section_number(current_group_key)
    return (
        section_major is not None
        and current_major is not None
        and section_major == current_major
    )


def _is_numbered_subsection(value: str | None) -> bool:
    parsed = _section_number(value)
    return parsed is not None and len(parsed) > 1


def _is_document_terminal_heading(value: str) -> bool:
    return value.strip().lower() in REFERENCE_HEADINGS


def _major_section_number(value: str | None) -> str | None:
    parsed = _section_number(value)
    return parsed[0] if parsed else None


def _section_number(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    match = re.match(r"^\s*(\d+(?:\.\d+)*)(?:[.)])?(?=\s+\S)", value)
    if match is None:
        return None
    return tuple(match.group(1).split("."))
