import httpx

from app.main import create_app
from tests.conftest import PASSWORD, auth, create_inbox


async def test_security_headers_on_api_responses(client: httpx.AsyncClient):
    response = await client.get("/api/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"


async def test_docs_are_disabled_by_default(client: httpx.AsyncClient):
    assert (await client.get("/docs")).status_code == 404
    assert (await client.get("/openapi.json")).status_code == 404


async def test_docs_enabled_by_setting(make_settings):
    app = create_app(make_settings(enable_docs=True))
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            assert (await client.get("/openapi.json")).status_code == 200


async def test_cors_allows_configured_origin_only_without_credentials(client: httpx.AsyncClient):
    allowed = await client.options(
        "/api/inboxes",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-credentials" not in allowed.headers

    denied = await client.options(
        "/api/inboxes",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in denied.headers


async def test_unhandled_error_returns_generic_500(make_settings):
    app = create_app(make_settings())

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("database password is hunter2")

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/boom")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "hunter2" not in response.text


async def test_validation_error_detail_is_a_string(client: httpx.AsyncClient):
    response = await client.post("/api/inboxes", json={"password": "short"})
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


async def test_inbox_detail_includes_capture_key(client: httpx.AsyncClient):
    session = await create_inbox(client)
    response = await client.get(f"/api/inboxes/{session['inbox']['id']}", headers=auth(session))
    assert response.status_code == 200
    assert "ingest_key" in response.json()


async def test_password_hash_is_never_serialized(client: httpx.AsyncClient):
    session = await create_inbox(client)
    body = (await client.get(f"/api/inboxes/{session['inbox']['id']}", headers=auth(session))).text
    assert "argon2" not in body
    assert PASSWORD not in body
