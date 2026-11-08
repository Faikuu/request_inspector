import base64
import json

import httpx

from tests.conftest import auth, create_inbox


def _capture_url(session: dict) -> str:
    return f"/api/hook/{session['inbox']['ingest_key']}"


async def _get_request(client: httpx.AsyncClient, session: dict, request_id: int) -> dict:
    response = await client.get(
        f"/api/inboxes/{session['inbox']['id']}/requests/{request_id}", headers=auth(session)
    )
    assert response.status_code == 200, response.text
    return response.json()


async def test_json_post_is_captured(client: httpx.AsyncClient):
    session = await create_inbox(client)
    response = await client.post(
        _capture_url(session),
        json={"order": 42},
        headers={"X-Trace": "abc", "Cookie": "sid=1"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    captured = await _get_request(client, session, response.json()["id"])

    assert captured["method"] == "POST"
    assert captured["path"] == "/"
    assert json.loads(captured["body"]) == {"order": 42}
    assert captured["body_base64"] is None
    assert captured["content_type"] == "application/json"
    assert captured["headers"]["x-trace"] == "abc"
    assert captured["headers"]["cookie"] == "sid=1"  # headers are kept for an inspector
    assert captured["size"] == len(json.dumps({"order": 42}, separators=(",", ":")))
    assert captured["remote_addr"] == "127.0.0.1"
    assert captured["created_at"].endswith("+00:00")


async def test_get_query_is_parsed_into_lists(client: httpx.AsyncClient):
    session = await create_inbox(client)
    response = await client.get(_capture_url(session), params=[("a", "1"), ("a", "2"), ("b", "x")])
    captured = await _get_request(client, session, response.json()["id"])

    assert captured["method"] == "GET"
    assert captured["query"] == {"a": ["1", "2"], "b": ["x"]}
    assert captured["body"] is None and captured["body_base64"] is None
    assert captured["size"] == 0


async def test_binary_body_is_base64(client: httpx.AsyncClient):
    session = await create_inbox(client)
    raw = bytes([0xFF, 0xD8, 0x00, 0x10, 0x80])
    response = await client.put(
        _capture_url(session), content=raw, headers={"Content-Type": "image/jpeg"}
    )
    captured = await _get_request(client, session, response.json()["id"])

    assert captured["body"] is None
    assert base64.b64decode(captured["body_base64"]) == raw
    assert captured["size"] == len(raw)


async def test_nul_bytes_are_stored_as_base64(client: httpx.AsyncClient):
    session = await create_inbox(client)
    response = await client.post(_capture_url(session), content=b"a\x00b")
    captured = await _get_request(client, session, response.json()["id"])
    assert captured["body"] is None
    assert base64.b64decode(captured["body_base64"]) == b"a\x00b"


async def test_sub_path_is_captured(client: httpx.AsyncClient):
    session = await create_inbox(client)
    key = session["inbox"]["ingest_key"]
    response = await client.patch(f"/api/hook/{key}/orders/42", json={"status": "shipped"})
    captured = await _get_request(client, session, response.json()["id"])

    assert captured["method"] == "PATCH"
    assert captured["path"] == "/orders/42"


async def test_all_methods_are_captured(client: httpx.AsyncClient):
    session = await create_inbox(client)
    key = session["inbox"]["ingest_key"]
    for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]:
        response = await client.request(method, f"/api/hook/{key}/m")
        assert response.status_code == 200, method
    head = await client.head(f"/api/hook/{key}")
    assert head.status_code == 200
    assert head.content == b""

    listed = await client.get(f"/api/inboxes/{session['inbox']['id']}/requests?limit=200", headers=auth(session))
    methods = [item["method"] for item in listed.json()["items"]]
    assert sorted(methods) == sorted(["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])


async def test_unknown_key_is_404(client: httpx.AsyncClient):
    response = await client.post("/api/hook/does-not-exist", json={})
    assert response.status_code == 404


async def test_oversize_body_is_413_when_declared(make_settings, tmp_path):
    from app.main import create_app

    app = create_app(make_settings(max_body_bytes=1024))
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            session = await create_inbox(client)
            url = f"/api/hook/{session['inbox']['ingest_key']}"
            big = await client.post(url, content=b"x" * 2048)
            assert big.status_code == 413
            ok = await client.post(url, content=b"x" * 1024)
            assert ok.status_code == 200


async def test_oversize_streamed_body_is_413(make_settings):
    from app.main import create_app

    app = create_app(make_settings(max_body_bytes=1024))
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            session = await create_inbox(client)
            url = f"/api/hook/{session['inbox']['ingest_key']}"

            async def chunks():
                for _ in range(10):
                    yield b"y" * 300

            response = await client.post(url, content=chunks())  # no Content-Length: chunked
            assert response.status_code == 413


async def test_hook_rate_limit(make_settings):
    from app.main import create_app

    app = create_app(make_settings(hook_requests_per_minute=2))
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            session = await create_inbox(client)
            url = f"/api/hook/{session['inbox']['ingest_key']}"
            assert (await client.post(url, json={})).status_code == 200
            assert (await client.post(url, json={})).status_code == 200
            limited = await client.post(url, json={})
            assert limited.status_code == 429
            assert "retry-after" in limited.headers


async def test_forwarded_for_only_when_proxy_trusted(make_settings):
    from app.main import create_app

    headers = {"X-Forwarded-For": "203.0.113.7, 10.0.0.1"}
    for trust, expected in [(False, "127.0.0.1"), (True, "203.0.113.7")]:
        app = create_app(make_settings(trust_proxy_headers=trust))
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                session = await create_inbox(client)
                response = await client.post(
                    f"/api/hook/{session['inbox']['ingest_key']}", json={}, headers=headers
                )
                captured = await _get_request(client, session, response.json()["id"])
                assert captured["remote_addr"] == expected


async def test_capture_cors_preflight_is_open(client: httpx.AsyncClient):
    session = await create_inbox(client)
    response = await client.options(
        f"/api/hook/{session['inbox']['ingest_key']}",
        headers={
            "Origin": "https://example.org",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 204
    assert response.headers["access-control-allow-origin"] == "*"
