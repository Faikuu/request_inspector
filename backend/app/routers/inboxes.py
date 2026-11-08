"""Inbox management, viewer sessions and captured request reads/deletes."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import get_db
from app.models import CapturedRequest, Inbox
from app.ratelimit import client_key, enforce
from app.schemas import (
    CapturedRequestOut,
    InboxCreate,
    InboxOut,
    InboxUpdate,
    PasswordIn,
    RequestPage,
    SessionOut,
    inbox_to_schema,
    request_to_schema,
)
from app.security import (
    DUMMY_HASH,
    create_viewer_token,
    hash_password,
    new_ingest_key,
    require_inbox,
    verify_password,
)

router = APIRouter(prefix="/api/inboxes", tags=["inboxes"])

INVALID_LOGIN = "Wrong inbox ID or password"
CLOSE_INBOX_GONE = 4404


async def _request_count(db: AsyncSession, inbox_id: str) -> int:
    count = await db.scalar(
        select(func.count()).select_from(CapturedRequest).where(CapturedRequest.inbox_id == inbox_id)
    )
    return int(count or 0)


def _session_out(settings: Settings, inbox: Inbox, request_count: int) -> SessionOut:
    token, expires_in = create_viewer_token(settings, inbox.id)
    return SessionOut(
        inbox=inbox_to_schema(inbox, request_count),
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
    )


async def _publish_inbox(request: Request, db: AsyncSession, inbox: Inbox, event_type: str) -> InboxOut:
    out = inbox_to_schema(inbox, await _request_count(db, inbox.id))
    await request.app.state.hub.broadcast(inbox.id, {"type": event_type, "data": out.model_dump(mode="json")})
    return out


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.post("", status_code=201, response_model=SessionOut)
async def create_inbox(body: InboxCreate, request: Request, db: AsyncSession = Depends(get_db)) -> SessionOut:
    await enforce(
        request.app.state.create_limiter,
        client_key(request),
        "You have created too many inboxes recently. Try again later.",
    )
    inbox = Inbox(
        name=body.name,
        password_hash=await asyncio.to_thread(hash_password, body.password),
        ingest_key=new_ingest_key(),
    )
    db.add(inbox)
    await db.commit()
    return _session_out(request.app.state.settings, inbox, 0)


@router.post("/{inbox_id}/session", response_model=SessionOut)
async def unlock_inbox(
    inbox_id: str, body: PasswordIn, request: Request, db: AsyncSession = Depends(get_db)
) -> SessionOut:
    await enforce(
        request.app.state.session_limiter,
        client_key(request),
        "Too many password attempts. Wait a minute and try again.",
    )
    # Also cap attempts per inbox across all clients, so spreading guesses over many IPs doesn't help.
    await enforce(
        request.app.state.inbox_session_limiter,
        f"inbox:{inbox_id[:64]}",
        "Too many password attempts for this inbox. Wait a minute and try again.",
    )
    inbox = await db.get(Inbox, inbox_id)
    # Always run one verify so a missing inbox and a wrong password take the same time.
    stored_hash = inbox.password_hash if inbox is not None else DUMMY_HASH
    matched = await asyncio.to_thread(verify_password, stored_hash, body.password)
    if inbox is None or not matched:
        raise HTTPException(status_code=401, detail=INVALID_LOGIN)
    return _session_out(request.app.state.settings, inbox, await _request_count(db, inbox.id))


@router.get("/{inbox_id}", response_model=InboxOut)
async def get_inbox(
    inbox: Inbox = Depends(require_inbox), db: AsyncSession = Depends(get_db)
) -> InboxOut:
    return inbox_to_schema(inbox, await _request_count(db, inbox.id))


@router.patch("/{inbox_id}", response_model=InboxOut)
async def rename_inbox(
    body: InboxUpdate,
    request: Request,
    inbox: Inbox = Depends(require_inbox),
    db: AsyncSession = Depends(get_db),
) -> InboxOut:
    inbox.name = body.name
    await db.commit()
    return await _publish_inbox(request, db, inbox, "inbox.updated")


@router.delete("/{inbox_id}", status_code=204)
async def delete_inbox(
    request: Request, inbox: Inbox = Depends(require_inbox), db: AsyncSession = Depends(get_db)
) -> None:
    await db.execute(delete(Inbox).where(Inbox.id == inbox.id))  # captured requests cascade
    await db.commit()
    hub = request.app.state.hub
    await hub.broadcast(inbox.id, {"type": "inbox.deleted"})
    await hub.close_all(inbox.id, CLOSE_INBOX_GONE)


@router.post("/{inbox_id}/rotate-key", response_model=InboxOut)
async def rotate_key(
    request: Request, inbox: Inbox = Depends(require_inbox), db: AsyncSession = Depends(get_db)
) -> InboxOut:
    inbox.ingest_key = new_ingest_key()
    await db.commit()
    return await _publish_inbox(request, db, inbox, "inbox.updated")


@router.get("/{inbox_id}/requests", response_model=RequestPage)
async def list_requests(
    inbox: Inbox = Depends(require_inbox),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    before_id: int | None = Query(None, ge=1),
    method: str | None = Query(None, min_length=1, max_length=32),
    q: str | None = Query(None, max_length=200),
) -> RequestPage:
    stmt = select(CapturedRequest).where(CapturedRequest.inbox_id == inbox.id)
    if before_id is not None:
        stmt = stmt.where(CapturedRequest.id < before_id)
    if method:
        stmt = stmt.where(CapturedRequest.method == method.upper())
    if q and q.strip():
        pattern = f"%{_escape_like(q.strip())}%"
        stmt = stmt.where(
            or_(
                CapturedRequest.path.ilike(pattern, escape="\\"),
                CapturedRequest.body.ilike(pattern, escape="\\"),
                CapturedRequest.headers.ilike(pattern, escape="\\"),
            )
        )
    rows = list((await db.scalars(stmt.order_by(CapturedRequest.id.desc()).limit(limit + 1))).all())
    has_more = len(rows) > limit
    return RequestPage(items=[request_to_schema(row) for row in rows[:limit]], has_more=has_more)


@router.get("/{inbox_id}/requests/{request_id}", response_model=CapturedRequestOut)
async def get_request(
    request_id: int,
    inbox: Inbox = Depends(require_inbox),
    db: AsyncSession = Depends(get_db),
) -> CapturedRequestOut:
    row = await db.scalar(
        select(CapturedRequest).where(CapturedRequest.id == request_id, CapturedRequest.inbox_id == inbox.id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return request_to_schema(row)


@router.delete("/{inbox_id}/requests/{request_id}", status_code=204)
async def delete_request(
    request_id: int,
    request: Request,
    inbox: Inbox = Depends(require_inbox),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(CapturedRequest).where(
            CapturedRequest.id == request_id, CapturedRequest.inbox_id == inbox.id
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    await db.commit()
    await request.app.state.hub.broadcast(inbox.id, {"type": "request.deleted", "id": request_id})


@router.delete("/{inbox_id}/requests", status_code=204)
async def clear_requests(
    request: Request, inbox: Inbox = Depends(require_inbox), db: AsyncSession = Depends(get_db)
) -> None:
    await db.execute(delete(CapturedRequest).where(CapturedRequest.inbox_id == inbox.id))
    await db.commit()
    await request.app.state.hub.broadcast(inbox.id, {"type": "requests.cleared"})


@router.get("/{inbox_id}/export")
async def export_requests(
    inbox: Inbox = Depends(require_inbox), db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    rows = (
        await db.scalars(
            select(CapturedRequest)
            .where(CapturedRequest.inbox_id == inbox.id)
            .order_by(CapturedRequest.id.desc())
        )
    ).all()
    payload = [request_to_schema(row).model_dump(mode="json") for row in rows]
    return JSONResponse(
        payload,
        headers={"Content-Disposition": f'attachment; filename="inbox-{inbox.id}.json"'},
    )
