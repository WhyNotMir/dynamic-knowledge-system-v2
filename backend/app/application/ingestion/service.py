from __future__ import annotations

import hashlib
import uuid
from functools import lru_cache
from typing import TypedDict

from langgraph.graph import END, StateGraph
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.ingestion.extractor import extract_pdf
from app.domain.ingestion.segmentor import FragmentData
from app.domain.ingestion.segmentor import segment_elements
from app.domain.ingestion.source_metadata import source_title_from_elements
from app.domain.ingestion.types import ExtractedElement
from app.domain.source import SourceStatus
from app.models.source import Source
from app.models.source_fragment import SourceFragment
from app.repositories.sources import SourceRepository


SAFE_INGESTION_ERROR = "Source processing failed. Check server logs for details."


def content_hash(content: str) -> str:
    normalized = " ".join(content.split()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class IngestionState(TypedDict, total=False):
    source_id: uuid.UUID
    db: AsyncSession
    source: Source | None
    elements: list[ExtractedElement]
    fragments_data: list[FragmentData]
    not_found: bool
    fragment_count: int


async def ingest_source(source_id: uuid.UUID, db: AsyncSession) -> Source | None:
    try:
        result = await _ingestion_graph().ainvoke({"source_id": source_id, "db": db})
        return result.get("source")
    except Exception as exc:
        sources = SourceRepository(db)
        source = await sources.get(source_id)
        if source is None:
            raise
        logger.exception(f"Source {source_id} ingestion failed: {exc}")
        return await sources.update_status(source, SourceStatus.FAILED, SAFE_INGESTION_ERROR)


async def _load_source(state: IngestionState) -> IngestionState:
    source_id = state["source_id"]
    db = state["db"]
    sources = SourceRepository(db)
    source = await sources.get(source_id)
    return {"source": source, "not_found": source is None}


def _route_after_load(state: IngestionState) -> str:
    return "missing" if state.get("not_found") else "continue"


async def _mark_processing(state: IngestionState) -> IngestionState:
    sources = SourceRepository(state["db"])
    source = state["source"]
    if source is None:
        return {"source": None, "not_found": True}

    updated = await sources.update_status(source, SourceStatus.PROCESSING, None)
    return {"source": updated}


async def _extract_elements(state: IngestionState) -> IngestionState:
    source = state["source"]
    if source is None:
        return {"not_found": True}
    return {"elements": extract_pdf(source.storage_path)}


async def _update_source_title(state: IngestionState) -> IngestionState:
    source = state["source"]
    if source is None:
        return {"not_found": True}
    sources = SourceRepository(state["db"])
    updated = await sources.update_title(source, source_title_from_elements(state["elements"]))
    return {"source": updated}


async def _segment_elements(state: IngestionState) -> IngestionState:
    return {"fragments_data": segment_elements(state["elements"])}


async def _save_fragments(state: IngestionState) -> IngestionState:
    source = state["source"]
    if source is None:
        return {"not_found": True}
    sources = SourceRepository(state["db"])
    fragments = [
        SourceFragment(
            source_id=source.id,
            content=fragment.content,
            content_hash=content_hash(fragment.content),
            element_type=fragment.element_type,
            position_index=fragment.position_index,
            page_number=fragment.page_number,
            heading_level=fragment.heading_level,
            section_path=fragment.section_path,
            meta_json=fragment.meta_json,
        )
        for fragment in state["fragments_data"]
    ]
    await sources.replace_fragments(source.id, fragments)
    return {"fragment_count": len(fragments)}


async def _mark_done(state: IngestionState) -> IngestionState:
    source = state["source"]
    if source is None:
        return {"not_found": True}
    sources = SourceRepository(state["db"])
    updated = await sources.update_status(source, SourceStatus.DONE, None)
    return {"source": updated}


@lru_cache(maxsize=1)
def _ingestion_graph():
    graph = StateGraph(IngestionState)
    graph.add_node("load_source", _load_source)
    graph.add_node("mark_processing", _mark_processing)
    graph.add_node("extract_elements", _extract_elements)
    graph.add_node("update_source_title", _update_source_title)
    graph.add_node("segment_elements", _segment_elements)
    graph.add_node("save_fragments", _save_fragments)
    graph.add_node("mark_done", _mark_done)

    graph.set_entry_point("load_source")
    graph.add_conditional_edges(
        "load_source",
        _route_after_load,
        {
            "continue": "mark_processing",
            "missing": END,
        },
    )
    graph.add_edge("mark_processing", "extract_elements")
    graph.add_edge("extract_elements", "update_source_title")
    graph.add_edge("update_source_title", "segment_elements")
    graph.add_edge("segment_elements", "save_fragments")
    graph.add_edge("save_fragments", "mark_done")
    graph.add_edge("mark_done", END)
    return graph.compile()
