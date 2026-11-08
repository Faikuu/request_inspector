"""In-memory sliding-window rate limiting and client address helpers."""

import asyncio
import math
import time
from collections import deque
from collections.abc import Callable

from fastapi import HTTPException, Request

from app.config import Settings


class SlidingWindowLimiter:
    """Allow at most `limit` hits per key in any `window_seconds` span. Single process only."""

    def __init__(
        self,
        limit: int,
        window_seconds: float,
        *,
        clock: Callable[[], float] = time.monotonic,
        sweep_every: int = 1024,
    ) -> None:
        self.limit = limit
        self.window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()
        self._ops = 0
        self._sweep_every = sweep_every

    async def hit(self, key: str) -> int | None:
        """Record a hit. Returns None when allowed, otherwise seconds until the next slot opens."""
        async with self._lock:
            now = self._clock()
            self._ops += 1
            if self._ops % self._sweep_every == 0:
                self._sweep(now)
            hits = self._hits.setdefault(key, deque())
            self._prune(hits, now)
            if len(hits) >= self.limit:
                return max(1, math.ceil(hits[0] + self.window - now))
            hits.append(now)
            return None

    def _prune(self, hits: deque[float], now: float) -> None:
        cutoff = now - self.window
        while hits and hits[0] <= cutoff:
            hits.popleft()

    def _sweep(self, now: float) -> None:
        for key in list(self._hits):
            hits = self._hits[key]
            self._prune(hits, now)
            if not hits:
                del self._hits[key]


def client_ip(request: Request, settings: Settings) -> str | None:
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "")
        first = forwarded.split(",")[0].strip()
        if first:
            return first[:64]
    return request.client.host if request.client else None


def client_key(request: Request) -> str:
    return client_ip(request, request.app.state.settings) or "unknown"


async def enforce(limiter: SlidingWindowLimiter, key: str, detail: str) -> None:
    retry_after = await limiter.hit(key)
    if retry_after is not None:
        raise HTTPException(status_code=429, detail=detail, headers={"Retry-After": str(retry_after)})
