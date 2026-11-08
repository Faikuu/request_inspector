"""Capture endpoint. The ingest key in the URL is the only credential."""

import base64
import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import CapturedRequest, Inbox, utcnow
from app.ratelimit import client_ip, enforce
from app.schemas import request_to_schema

HOOK_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
# Stored header bytes per request. Headers past this budget are dropped, the body is unaffected.
MAX_STORED_HEADER_BYTES = 16 * 1024

router = APIRouter(prefix="/api/hook", tags=["hook"])


def _too_large(limit: int) -> HTTPException:
    return HTTPException(status_code=413, detail=f"Request body is larger than {limit} bytes")


async def _read_body(request: Request, limit: int) -> bytes:
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            length = int(declared)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid Content-Length header") from None
        if length < 0:
            raise HTTPException(status_code=400, detail="Invalid Content-Length header")
        if length > limit:
            raise _too_large(limit)
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > limit:
            raise _too_large(limit)
        chunks.append(chunk)
    return b"".join(chunks)


def _encode_body(raw: bytes) -> tuple[str | None, str | None]:
    """(text, base64). Text when the body is valid UTF-8 without NUL bytes, base64 otherwise."""
    if not raw:
        return None, None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, base64.b64encode(raw).decode("ascii")
    if "\x00" in text:
        return None, base64.b64encode(raw).decode("ascii")
    return text, None


def _headers_dict(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {}
    used = 0
    for name, value in request.headers.items():
        name = name.lower()
        if name in headers:
            cost = len(value) + 2
            if used + cost > MAX_STORED_HEADER_BYTES:
                continue
            headers[name] += ", " + value
        else:
            cost = len(name) + len(value)
            if used + cost > MAX_STORED_HEADER_BYTES:
                continue
            headers[name] = value
        used += cost
    return headers


def _query_dict(request: Request) -> dict[str, list[str]]:
    query: dict[str, list[str]] = {}
    for key, value in request.query_params.multi_items():
        query.setdefault(key, []).append(value)
    return query


async def _prune(db: AsyncSession, inbox_id: str, keep: int) -> None:
    """Delete everything older than the newest `keep` requests, in one statement."""
    cutoff = (
        select(CapturedRequest.id)
        .where(CapturedRequest.inbox_id == inbox_id)
        .order_by(CapturedRequest.id.desc())
        .offset(keep)
        .limit(1)
        .scalar_subquery()
    )
    await db.execute(
        delete(CapturedRequest).where(CapturedRequest.inbox_id == inbox_id, CapturedRequest.id <= cutoff)
    )


@router.api_route("/{ingest_key}", methods=HOOK_METHODS, include_in_schema=False)
@router.api_route("/{ingest_key}/{path:path}", methods=HOOK_METHODS, include_in_schema=False)
async def capture(
    request: Request,
    background: BackgroundTasks,
    ingest_key: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    settings = request.app.state.settings
    inbox = await db.scalar(select(Inbox).where(Inbox.ingest_key == ingest_key))
    if inbox is None:
        raise HTTPException(status_code=404, detail="Not found")
    await enforce(request.app.state.hook_limiter, f"hook:{inbox.id}", "Too many requests for this inbox. Slow down.")

    raw = await _read_body(request, settings.max_body_bytes)
    body, body_base64 = _encode_body(raw)
    sub_path = request.path_params.get("path", "").replace("\x00", "�")
    row = CapturedRequest(
        inbox_id=inbox.id,
        method=request.method,
        path="/" + sub_path,
        query=json.dumps(_query_dict(request)),
        headers=json.dumps(_headers_dict(request)),
        content_type=request.headers.get("content-type"),
        body=body,
        body_base64=body_base64,
        size=len(raw),
        remote_addr=client_ip(request, settings),
        created_at=utcnow(),
    )
    db.add(row)
    await db.flush()
    await _prune(db, inbox.id, settings.max_requests_per_inbox)
    await db.commit()

    event = {"type": "request.created", "data": request_to_schema(row).model_dump(mode="json")}
    background.add_task(request.app.state.hub.broadcast, inbox.id, event)
    response: Response
    if request.method == "HEAD":
        response = Response(status_code=200)
    else:
        response = JSONResponse({"ok": True, "id": row.id})
    response.background = background
    return response
