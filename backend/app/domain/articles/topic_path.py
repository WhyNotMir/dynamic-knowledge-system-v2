from __future__ import annotations

import re


def article_topic_path(*, title: str, section_paths: list[str | None]) -> list[str]:
    for section_path in section_paths:
        parts = _path_parts(section_path)
        if parts:
            return parts

    cleaned_title = clean_heading_label(title)
    return [cleaned_title] if cleaned_title else ["Untitled"]


def clean_heading_label(value: str) -> str:
    text = " ".join(value.split()).strip()
    return re.sub(r"^\d+(?:\.\d+)*(?:[.)])?\s+", "", text)


def _path_parts(section_path: str | None) -> list[str]:
    return [
        cleaned
        for part in (section_path or "").split(">")
        if (cleaned := clean_heading_label(part))
    ]
