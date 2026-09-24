"""Tag CRUD + note-tag association endpoints (Task 3)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Note, Tag
from ..schemas import TagAddRequest, TagCreate, TagRead

router = APIRouter(prefix="/tags", tags=["tags"])


def _get_or_create_tag(db: Session, name: str) -> Tag:
    name = name.strip().lower()
    if not name:
        raise HTTPException(status_code=422, detail="tag name must be non-empty")
    tag = db.execute(select(Tag).where(Tag.name == name)).scalar_one_or_none()
    if tag is None:
        tag = Tag(name=name)
        db.add(tag)
        db.flush()
    return tag


@router.get("/", response_model=list[TagRead])
def list_tags(db: Session = Depends(get_db)) -> list[TagRead]:
    tags = db.execute(select(Tag).order_by(Tag.name)).scalars().all()
    return [TagRead.model_validate(t) for t in tags]


@router.post("/", response_model=TagRead, status_code=201)
def create_tag(payload: TagCreate, db: Session = Depends(get_db)) -> TagRead:
    existing = db.execute(select(Tag).where(Tag.name == payload.name.strip().lower())).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"tag '{payload.name}' already exists")
    tag = _get_or_create_tag(db, payload.name)
    return TagRead.model_validate(tag)


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: int, db: Session = Depends(get_db)) -> None:
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)  # join rows cascade
    db.flush()


@router.post("/notes/{note_id}", response_model=list[TagRead])
def attach_tags(note_id: int, payload: TagAddRequest, db: Session = Depends(get_db)) -> list[TagRead]:
    """Attach one or more tags to a note (idempotent per tag)."""
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    current = {t.name for t in note.tags}
    for name in payload.names:
        tag = _get_or_create_tag(db, name)
        if tag.name not in current:
            note.tags.append(tag)
            current.add(tag.name)
    db.flush()
    return [TagRead.model_validate(t) for t in note.tags]
