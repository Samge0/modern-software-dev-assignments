"""Notes CRUD API — FastAPI + SQLAlchemy (Version 2).

Same functional scope as v1-flask; showcases typed schemas, automatic
validation, and OpenAPI docs. Run: uvicorn app:app --port 5002
"""
from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Integer, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DB_URL = "sqlite:///./notes.db"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class NoteRead(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


app = FastAPI(title="Notes API v2 — FastAPI")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/notes", response_model=list[NoteRead])
def list_notes():
    with SessionLocal() as db:
        rows = db.execute(select(Note).order_by(Note.id.desc())).scalars().all()
        return [NoteRead.model_validate(r) for r in rows]


@app.post("/notes", response_model=NoteRead, status_code=201)
def create_note(payload: NoteCreate):
    with SessionLocal() as db:
        note = Note(title=payload.title, content=payload.content)
        db.add(note)
        db.commit()
        db.refresh(note)
        return NoteRead.model_validate(note)


@app.get("/notes/{note_id}", response_model=NoteRead)
def get_note(note_id: int):
    with SessionLocal() as db:
        note = db.get(Note, note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="note not found")
        return NoteRead.model_validate(note)


@app.put("/notes/{note_id}", response_model=NoteRead)
def update_note(note_id: int, payload: NoteCreate):
    with SessionLocal() as db:
        note = db.get(Note, note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="note not found")
        note.title = payload.title
        note.content = payload.content
        db.commit()
        db.refresh(note)
        return NoteRead.model_validate(note)


@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int):
    with SessionLocal() as db:
        note = db.get(Note, note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="note not found")
        db.delete(note)
        db.commit()
