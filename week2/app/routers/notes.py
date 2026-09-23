from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from .. import db
from ..schemas import NoteCreate, NoteList, NoteOut

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteOut)
def create_note(payload: NoteCreate) -> dict:
    note_id = db.insert_note(payload.content.strip())
    note = db.get_note(note_id)
    return {"id": note["id"], "content": note["content"], "created_at": note["created_at"]}


@router.get("", response_model=NoteList)
def list_notes() -> dict:
    """List all notes (TODO 4.2)."""
    rows = db.list_notes()
    return {"notes": [{"id": r["id"], "content": r["content"], "created_at": r["created_at"]} for r in rows]}


@router.get("/{note_id}", response_model=NoteOut)
def get_single_note(note_id: int) -> dict:
    row = db.get_note(note_id)
    if row is None:
        raise HTTPException(status_code=404, detail="note not found")
    return {"id": row["id"], "content": row["content"], "created_at": row["created_at"]}
