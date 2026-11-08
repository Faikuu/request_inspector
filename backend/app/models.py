"""ORM models: inboxes and the requests captured into them."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_inbox_id() -> str:
    return str(uuid.uuid4())


class Inbox(Base):
    __tablename__ = "inboxes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_inbox_id)
    name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    # Secret part of the capture URL. Rotating it breaks the old URL.
    ingest_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class CapturedRequest(Base):
    __tablename__ = "captured_requests"
    __table_args__ = (Index("ix_captured_requests_inbox_id_id", "inbox_id", "id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inbox_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("inboxes.id", ondelete="CASCADE"), nullable=False
    )
    method: Mapped[str] = mapped_column(Text, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON text: {name: [value, ...]}
    query: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    # JSON text: {lowercase-name: value}
    headers: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    content_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    remote_addr: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
