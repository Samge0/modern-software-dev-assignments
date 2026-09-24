"""Pydantic schemas defining the API contract (refactor TODO 3).

Replaces ad-hoc `Dict[str, Any]` payloads in the routers with typed models so
the contract is declared once, validated by FastAPI, and surfaced in /docs.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Free-form note text")


class NoteOut(BaseModel):
    id: int
    content: str
    created_at: str


class NoteList(BaseModel):
    notes: List[NoteOut]


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Free-form text to extract action items from")
    save_note: bool = Field(False, description="Persist the source text as a note")


class ExtractRequestLLM(ExtractRequest):
    """Same shape as ExtractRequest; LLM engine selected by endpoint."""


class ActionItemOut(BaseModel):
    id: int
    text: str
    note_id: Optional[int] = None


class ExtractResponse(BaseModel):
    engine: str = "heuristic"
    note_id: Optional[int] = None
    items: List[ActionItemOut]


class ActionItemList(BaseModel):
    items: List[ActionItemOutFull]


class ActionItemOutFull(BaseModel):
    id: int
    note_id: Optional[int] = None
    text: str
    done: bool
    created_at: str


class MarkDoneRequest(BaseModel):
    done: bool = True


class MarkDoneResponse(BaseModel):
    id: int
    done: bool


class HealthResponse(BaseModel):
    status: str = "ok"
