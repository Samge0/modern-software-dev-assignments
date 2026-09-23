from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from .. import db
from ..schemas import (
    ActionItemOutFull,
    ExtractRequest,
    ExtractResponse,
    MarkDoneRequest,
    MarkDoneResponse,
    NoteCreate,
    NoteList,
    NoteOut,
)
from ..services.extract import extract_action_items
from ..services.extract_llm import extract_action_items_llm

router = APIRouter(prefix="/action-items", tags=["action-items"])


def _extract(payload: ExtractRequest, engine: str) -> dict:
    """Shared extraction flow for both engines."""
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    note_id: Optional[int] = None
    if payload.save_note:
        note_id = db.insert_note(text)

    if engine == "llm":
        try:
            items = extract_action_items_llm(text)
        except Exception as exc:  # noqa: BLE001 - surface upstream LLM failures as 502
            raise HTTPException(status_code=502, detail=f"LLM extraction failed: {exc}") from exc
    else:
        items = extract_action_items(text)

    ids = db.insert_action_items(items, note_id=note_id)
    return {
        "engine": engine,
        "note_id": note_id,
        "items": [{"id": i, "text": t} for i, t in zip(ids, items)],
    }


@router.post("/extract", response_model=ExtractResponse)
def extract(payload: ExtractRequest) -> dict:
    """Heuristic extraction (original behaviour, now typed)."""
    return _extract(payload, engine="heuristic")


@router.post("/extract-llm", response_model=ExtractResponse)
def extract_llm(payload: ExtractRequest) -> dict:
    """LLM-powered extraction (TODO 4.1)."""
    return _extract(payload, engine="llm")


@router.get("", response_model=List[ActionItemOutFull])
def list_all(note_id: Optional[int] = None) -> List[Dict[str, Any]]:
    rows = db.list_action_items(note_id=note_id)
    return [
        {
            "id": r["id"],
            "note_id": r["note_id"],
            "text": r["text"],
            "done": bool(r["done"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


@router.post("/{action_item_id}/done", response_model=MarkDoneResponse)
def mark_done(action_item_id: int, payload: MarkDoneRequest) -> Dict[str, Any]:
    row = db.get_action_item(action_item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="action item not found")
    db.mark_action_item_done(action_item_id, payload.done)
    return {"id": action_item_id, "done": payload.done}
