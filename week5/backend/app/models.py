from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    # Python-side default for ORM inserts, server default for raw SQL (seed.sql)
    created_at = Column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now(), nullable=False
    )


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
