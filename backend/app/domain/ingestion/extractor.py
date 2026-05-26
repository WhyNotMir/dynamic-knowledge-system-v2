from __future__ import annotations

import base64
import io
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from PIL import ImageOps

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
    for option_name in ("generate_picture_images", "generate_page_images", "images_scale"):
        if hasattr(pdf_options, option_name):
            setattr(pdf_options, option_name, True if option_name != "images_scale" else 1.5)

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
            rows = _table_rows(item, document)
            content = _table_content(rows, text)
            element_type = ElementType.TABLE
            heading_level = None
            meta_json = _base_meta(item, label)
            meta_json["table"] = {
                "rows": rows,
                "plain_text": content,
                "display_mode": "grid" if rows else "text",
            }
        elif label in {"picture", "figure"}:
            image_payload = _picture_payload(item, document)
            content = _caption_text(item) or "Source figure"
            element_type = ElementType.IMAGE
            heading_level = None
            meta_json = _base_meta(item, label)
            meta_json["image"] = {
                "has_payload": image_payload is not None,
                "bbox": meta_json.get("docling", {}).get("bbox"),
            }
            if image_payload:
                meta_json.update(image_payload)
        else:
            if not text:
                continue

            element_type, heading_level = _classify_text(
                label=label,
                text=text,
                raw_level=raw_level,
                in_references=in_references,
            )
            meta_json = _base_meta(item, label)

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

    return _attach_captions(elements)


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

    if label in {"blockquote", "quote"}:
        return ElementType.QUOTE, None

    if label in {"code", "code_block"}:
        return ElementType.CODE_BLOCK, None

    if label == "footnote":
        return ElementType.FOOTNOTE, None

    if label in {"formula", "equation"}:
        return ElementType.FORMULA, None

    if _looks_like_caption(text):
        return ElementType.CAPTION, None

    return ElementType.PARAGRAPH, None


def _label_value(item: Any) -> str:
    label = getattr(item, "label", "")
    value = getattr(label, "value", label)
    return str(value).lower()


def _base_meta(item: Any, label: str) -> dict[str, Any]:
    page_number = _page_number(item)
    bbox = _bbox_dict(getattr(_first_provenance(item), "bbox", None))
    docling: dict[str, Any] = {"label": label}
    if page_number is not None:
        docling["page"] = {"number": page_number}
    if bbox:
        docling["bbox"] = bbox
    return {
        "source_label": label,
        "docling": docling,
    }


def _table_rows(item: Any, document: Any) -> list[list[str]]:
    try:
        dataframe = item.export_to_dataframe(doc=document)
    except Exception:
        return []

    rows: list[list[str]] = []
    for row in dataframe.fillna("").astype(str).values.tolist():
        cleaned = [_normalise_text(cell) for cell in row]
        if any(cleaned):
            rows.append(cleaned)
    return rows


def _table_content(rows: list[list[str]], fallback_text: str) -> str:
    plain_text = "\n".join(" | ".join(cell for cell in row if cell) for row in rows).strip()
    return plain_text or fallback_text or "Table"


def _picture_payload(item: Any, document: Any) -> dict[str, Any] | None:
    image = getattr(item, "image", None)
    pil_image = getattr(image, "pil_image", None) or getattr(item, "pil_image", None)
    if pil_image is None:
        get_image = getattr(item, "get_image", None)
        if callable(get_image):
            try:
                pil_image = get_image(document)
            except Exception:
                try:
                    pil_image = get_image()
                except Exception:
                    pil_image = None

    if pil_image is None:
        return None

    pil_image = ImageOps.exif_transpose(pil_image)
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return {
        "image_base64": base64.b64encode(buffer.getvalue()).decode("ascii"),
        "image_ext": "png",
        "image_width": pil_image.width,
        "image_height": pil_image.height,
    }


def _caption_text(item: Any) -> str | None:
    caption_text = getattr(item, "caption_text", None)
    if isinstance(caption_text, str) and caption_text.strip():
        return _normalise_text(caption_text)
    return None


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
    first = _first_provenance(item)
    if first is None:
        return None
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


def _attach_captions(elements: list[ExtractedElement]) -> list[ExtractedElement]:
    for index, element in enumerate(elements):
        if element.element_type != ElementType.CAPTION:
            continue
        target_index = _caption_target_index(elements, index)
        if target_index is None:
            continue

        group_id = f"caption-{index}-{target_index}"
        target = elements[target_index]
        target_kind = "image" if target.element_type == ElementType.IMAGE else "table"
        caption_meta = {
            "caption_group_id": group_id,
            "caption": {"target_kind": target_kind, "text": element.content},
        }
        element.meta_json = {**(element.meta_json or {}), **caption_meta}
        target.meta_json = {**(target.meta_json or {}), **caption_meta}
    return elements


def _caption_target_index(elements: list[ExtractedElement], caption_index: int) -> int | None:
    preferred = (
        ElementType.IMAGE
        if re.match(r"^(?i:figure|fig\.?)\s+", elements[caption_index].content)
        else ElementType.TABLE
    )
    for offset in (1, 2, 3, -1, -2, -3):
        index = caption_index + offset
        if 0 <= index < len(elements) and elements[index].element_type == preferred:
            return index
    for offset in (1, 2, 3, -1, -2, -3):
        index = caption_index + offset
        if 0 <= index < len(elements) and elements[index].element_type in {
            ElementType.TABLE,
            ElementType.IMAGE,
        }:
            return index
    return None


def _first_provenance(item: Any) -> Any | None:
    prov = getattr(item, "prov", None)
    if not prov:
        return None
    return prov[0] if isinstance(prov, list) else prov


def _bbox_dict(bbox: Any) -> dict[str, float] | None:
    if bbox is None:
        return None
    values = [
        getattr(bbox, "l", None),
        getattr(bbox, "t", None),
        getattr(bbox, "r", None),
        getattr(bbox, "b", None),
    ]
    if any(value is None for value in values):
        return None
    left, top, right, bottom = (float(value) for value in values)
    return {
        "x0": min(left, right),
        "y0": min(top, bottom),
        "x1": max(left, right),
        "y1": max(top, bottom),
        "width": abs(right - left),
        "height": abs(bottom - top),
    }
