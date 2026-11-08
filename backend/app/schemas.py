"""Wire models. They match the API contract in the shared spec and frontend/src/api/types.ts."""

import json
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, Field, PlainSerializer

from app.models import CapturedRequest, Inbox

MAX_NAME_LENGTH = 80


def _ensure_utc(value: Any) -> Any:
    """SQLite returns naive datetimes. Everything stored is UTC, so treat naive values as UTC."""
    if not isinstance(value, datetime):
        return value
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


UtcDatetime = Annotated[
    datetime,
    BeforeValidator(_ensure_utc),
    PlainSerializer(lambda dt: dt.isoformat(), return_type=str, when_used="json"),
]


def _clean_name(value: Any) -> Any:
    if value is None or not isinstance(value, str):
        return value
    if "\x00" in value:
        raise ValueError("Name contains invalid characters")
    value = value.strip()
    return value or None


def _check_name_length(value: str | None) -> str | None:
    if value is not None and len(value) > MAX_NAME_LENGTH:
        raise ValueError(f"Name must be {MAX_NAME_LENGTH} characters or fewer")
    return value


InboxName = Annotated[str | None, BeforeValidator(_clean_name), AfterValidator(_check_name_length)]


class InboxCreate(BaseModel):
    password: str = Field(min_length=8, max_length=128)
    name: InboxName = None


class InboxUpdate(BaseModel):
    name: InboxName = None


class PasswordIn(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class InboxOut(BaseModel):
    id: str
    name: str | None
    ingest_key: str
    created_at: UtcDatetime
    request_count: int


class SessionOut(BaseModel):
    inbox: InboxOut
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class CapturedRequestOut(BaseModel):
    id: int
    inbox_id: str
    method: str
    path: str
    query: dict[str, list[str]]
    headers: dict[str, str]
    content_type: str | None
    body: str | None
    body_base64: str | None
    size: int
    remote_addr: str | None
    created_at: UtcDatetime


class RequestPage(BaseModel):
    items: list[CapturedRequestOut]
    has_more: bool


def inbox_to_schema(inbox: Inbox, request_count: int) -> InboxOut:
    return InboxOut(
        id=inbox.id,
        name=inbox.name,
        ingest_key=inbox.ingest_key,
        created_at=inbox.created_at,
        request_count=request_count,
    )


def request_to_schema(row: CapturedRequest) -> CapturedRequestOut:
    return CapturedRequestOut(
        id=row.id,
        inbox_id=row.inbox_id,
        method=row.method,
        path=row.path,
        query=json.loads(row.query or "{}"),
        headers=json.loads(row.headers or "{}"),
        content_type=row.content_type,
        body=row.body,
        body_base64=row.body_base64,
        size=row.size,
        remote_addr=row.remote_addr,
        created_at=row.created_at,
    )
