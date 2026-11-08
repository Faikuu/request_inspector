from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any

import httpx
import pytest

from app.config import Settings
from app.main import create_app

SECRET = "test-secret-key-that-is-long-enough-123456"
PASSWORD = "correct horse battery"
ORIGIN = "http://localhost:5173"


@pytest.fixture
def make_settings(tmp_path: Path) -> Callable[..., Settings]:
    """Settings with a private temp-file SQLite database. Keyword overrides win."""

    def _make(**overrides: Any) -> Settings:
        values: dict[str, Any] = {
            "secret_key": SECRET,
            "database_url": f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
        }
        values.update(overrides)
        return Settings(_env_file=None, **values)

    return _make


@pytest.fixture
async def client(make_settings: Callable[..., Settings]) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(make_settings())
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
            yield http


async def create_inbox(client: httpx.AsyncClient, name: str | None = None) -> dict[str, Any]:
    response = await client.post("/api/inboxes", json={"password": PASSWORD, "name": name})
    assert response.status_code == 201, response.text
    return response.json()


def auth(session: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['access_token']}"}
