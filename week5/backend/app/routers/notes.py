from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Note
from ..schemas import NoteCreate, NotePage, NoteRead, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])

SORT_COLUMNS = {
    "created_desc": (Note.created_at.desc(), Note.id.desc()),
    "created_asc": (Note.created_at.asc(), Note.id.asc()),
    "title_asc": (Note.title.asc(), Note.id.asc()),
    "title_desc": (Note.title.desc(), Note.id.desc()),
}


def _paginate(query, page: int, page_size: int, db: Session):
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    rows = (
        db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    )
    return rows, total


@router.get("/", response_model=NotePage)
def list_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> NotePage:
    query = select(Note)
    rows, total = _paginate(query.order_by(*SORT_COLUMNS["created_desc"]), page, page_size, db)
    return NotePage(
        items=[NoteRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=NoteRead, status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> NoteRead:
    note = Note(title=payload.title, content=payload.content)
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.get("/search/", response_model=NotePage)
def search_notes(
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort: str = Query("created_desc", pattern="^(created_desc|created_asc|title_asc|title_desc)$"),
    db: Session = Depends(get_db),
) -> NotePage:
    query = select(Note)
    if q:
        like = f"%{q}%"
        query = query.where(Note.title.ilike(like) | Note.content.ilike(like))
    rows, total = _paginate(query.order_by(*SORT_COLUMNS[sort]), page, page_size, db)
    return NotePage(
        items=[NoteRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{note_id}", response_model=NoteRead)
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteRead.model_validate(note)


@router.put("/{note_id}", response_model=NoteRead)
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.title = payload.title
    note.content = payload.content
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)) -> None:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.flush()
