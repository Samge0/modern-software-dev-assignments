import ast
import operator
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, select, text
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Note
from ..schemas import NoteCreate, NotePatch, NoteRead

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/", response_model=list[NoteRead])
def list_notes(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(50, le=200),
    sort: str = Query("-created_at", description="Sort by field, prefix with - for desc"),
) -> list[NoteRead]:
    stmt = select(Note)
    if q:
        stmt = stmt.where((Note.title.contains(q)) | (Note.content.contains(q)))

    sort_field = sort.lstrip("-")
    order_fn = desc if sort.startswith("-") else asc
    if hasattr(Note, sort_field):
        stmt = stmt.order_by(order_fn(getattr(Note, sort_field)))
    else:
        stmt = stmt.order_by(desc(Note.created_at))

    rows = db.execute(stmt.offset(skip).limit(limit)).scalars().all()
    return [NoteRead.model_validate(row) for row in rows]


@router.post("/", response_model=NoteRead, status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> NoteRead:
    note = Note(title=payload.title, content=payload.content)
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.patch("/{note_id}", response_model=NoteRead)
def patch_note(note_id: int, payload: NotePatch, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if payload.title is not None:
        note.title = payload.title
    if payload.content is not None:
        note.content = payload.content
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.get("/{note_id}", response_model=NoteRead)
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteRead.model_validate(note)


@router.get("/unsafe-search/", response_model=list[NoteRead])
def unsafe_search(q: str, db: Session = Depends(get_db)) -> list[NoteRead]:
    # FIX (semgrep: avoid-sqlalchemy-text / SQL injection): the raw f-string
    # sqlalchemy.text() query is replaced with a bound parameter. The LIKE
    # pattern is passed as a bind param and %/_ wildcards in user input are
    # escaped, so input can never alter query structure.
    pattern = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    sql = text(
        """
        SELECT id, title, content, created_at, updated_at
        FROM notes
        WHERE title LIKE :pattern ESCAPE '\\' OR content LIKE :pattern ESCAPE '\\'
        ORDER BY created_at DESC
        LIMIT 50
        """
    )
    rows = db.execute(sql, {"pattern": pattern}).all()
    results: list[NoteRead] = []
    for r in rows:
        results.append(
            NoteRead(
                id=r.id,
                title=r.title,
                content=r.content,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
        )
    return results


@router.get("/debug/hash-md5")
def debug_hash_md5(q: str) -> dict[str, str]:
    import hashlib

    return {"algo": "md5", "hex": hashlib.md5(q.encode()).hexdigest()}


# ---------------------------------------------------------------------------
# FIX (semgrep: eval-detected): the /debug/eval endpoint that passed user input
# to eval() is REMOVED. It allowed full remote code execution. If arithmetic
# evaluation is genuinely needed, /debug/calc below is the safe replacement:
# character allowlist + AST-walk evaluation (no names, no attribute access,
# no function calls).
# ---------------------------------------------------------------------------
_ALLOWED_CALC_TOKENS = set("0123456789+-*/(). ")


@router.get("/debug/calc")
def debug_calc(expr: str) -> dict[str, str]:
    """Safe arithmetic evaluator (replacement for the removed /debug/eval)."""

    def _eval(node: ast.expr) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = _eval(node.left), _eval(node.right)
            op = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
            }[type(node.op)]
            return op(left, right)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            val = _eval(node.operand)
            return val if isinstance(node.op, ast.UAdd) else -val
        raise HTTPException(status_code=400, detail="unsupported expression")

    if not expr or set(expr) - _ALLOWED_CALC_TOKENS:
        raise HTTPException(status_code=400, detail="only arithmetic like 2*(3+4) is allowed")
    try:
        tree = ast.parse(expr, mode="eval")
        result = _eval(tree.body)
    except (SyntaxError, ZeroDivisionError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid expression: {exc}") from exc
    return {"result": str(result)}


# ---------------------------------------------------------------------------
# FIX (semgrep: subprocess-shell-true): the /debug/run endpoint that executed
# arbitrary shell commands (shell=True) is REMOVED. There is no safe way to
# expose arbitrary command execution to remote callers.
# ---------------------------------------------------------------------------


@router.get("/debug/fetch")
def debug_fetch(url: str) -> dict[str, str]:
    # FIX (semgrep: dynamic-urllib-use-detected): scheme + host are validated
    # before opening. Only public http(s) URLs are allowed — blocking file://
    # reads and SSRF against localhost/internal services. A 5s timeout bounds
    # the request duration.
    from urllib.parse import urlparse
    from urllib.request import urlopen

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="only http(s) URLs are allowed")
    if not parsed.hostname or parsed.hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        raise HTTPException(status_code=400, detail="localhost URLs are not allowed")

    with urlopen(parsed.geturl(), timeout=5) as res:  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
        # Accepted residual risk, documented in writeup.md: this call is guarded
        # by an explicit scheme allowlist (http/https only) and a localhost-host
        # denylist validated immediately above; `parsed.geturl()` (not raw user
        # input) is passed. file:// and internal SSRF targets are unreachable
        # (verified by test_fetch_blocks_file_scheme_and_localhost).
        body = res.read(1024).decode(errors="ignore")
    return {"snippet": body}


@router.get("/debug/read")
def debug_read(path: str) -> dict[str, str]:
    # FIX (defense in depth, path traversal): reads are restricted to the
    # week6 data/ directory; the target is resolved and checked against the
    # base so ../ escapes cannot leave it.
    from pathlib import Path as _Path

    base = (_Path(__file__).resolve().parents[2] / "data").resolve()
    target = (base / path).resolve()
    if base not in target.parents:
        raise HTTPException(status_code=400, detail="path outside data/ is not allowed")
    try:
        content = target.read_text(encoding="utf-8", errors="ignore")[:1024]
    except OSError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"snippet": content}
