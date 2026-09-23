from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ActionItem
from ..schemas import (
    ActionItemBulkCompleteRequest,
    ActionItemBulkCompleteResponse,
    ActionItemCreate,
    ActionItemPage,
    ActionItemRead,
)

router = APIRouter(prefix="/action-items", tags=["action_items"])


@router.get("/", response_model=ActionItemPage)
def list_items(
    completed: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort: str = Query(
        "created_desc",
        pattern="^(created_desc|created_asc|description_asc|description_desc)$",
    ),
    db: Session = Depends(get_db),
) -> ActionItemPage:
    # TASK 4: completion filter; TASK 8: pagination on every collection.
    query = select(ActionItem)
    if completed is not None:
        query = query.where(ActionItem.completed.is_(completed))

    order = {
        "created_desc": (ActionItem.id.desc(),),
        "created_asc": (ActionItem.id.asc(),),
        "description_asc": (ActionItem.description.asc(), ActionItem.id.asc()),
        "description_desc": (ActionItem.description.desc(), ActionItem.id.desc()),
    }[sort]

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    rows = (
        db.execute(query.order_by(*order).offset((page - 1) * page_size).limit(page_size))
        .scalars()
        .all()
    )
    return ActionItemPage(
        items=[ActionItemRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=ActionItemRead, status_code=201)
def create_item(payload: ActionItemCreate, db: Session = Depends(get_db)) -> ActionItemRead:
    item = ActionItem(description=payload.description, completed=False)
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.put("/{item_id}/complete", response_model=ActionItemRead)
def complete_item(item_id: int, db: Session = Depends(get_db)) -> ActionItemRead:
    item = db.get(ActionItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    item.completed = True
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.post("/bulk-complete", response_model=ActionItemBulkCompleteResponse)
def bulk_complete(
    payload: ActionItemBulkCompleteRequest, db: Session = Depends(get_db)
) -> ActionItemBulkCompleteResponse:
    """TASK 4: mark many items complete in ONE transaction.

    All-or-nothing: if any id is unknown, nothing is written (the session
    rolls back via get_db's error path), and the client learns which ids were
    missing before any mutation happened.
    """
    ids = payload.ids
    if not ids:
        raise HTTPException(status_code=422, detail="ids must contain at least one id")

    found_rows = db.execute(select(ActionItem).where(ActionItem.id.in_(ids))).scalars().all()
    found_ids = {row.id for row in found_rows}
    missing = [i for i in ids if i not in found_ids]
    if missing:
        # Nothing has been mutated yet; raising triggers get_db rollback.
        raise HTTPException(
            status_code=404,
            detail={"message": "some action items not found", "missing_ids": missing},
        )

    for row in found_rows:
        row.completed = True
        db.add(row)
    db.flush()
    return ActionItemBulkCompleteResponse(updated_count=len(found_rows), ids=sorted(found_ids))
