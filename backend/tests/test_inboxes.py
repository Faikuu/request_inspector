import httpx

from tests.conftest import PASSWORD, auth, create_inbox


async def test_create_inbox_returns_session(client: httpx.AsyncClient):
    session = await create_inbox(client, name="  Orders  ")

    assert session["token_type"] == "bearer"
    assert session["expires_in"] == 3600
    inbox = session["inbox"]
    assert inbox["name"] == "Orders"
    assert inbox["request_count"] == 0
    assert len(inbox["id"]) == 36
    assert inbox["created_at"].endswith("+00:00")
    assert "password" not in inbox and "password_hash" not in inbox


async def test_blank_name_becomes_null_and_long_name_is_rejected(client: httpx.AsyncClient):
    session = await create_inbox(client, name="   ")
    assert session["inbox"]["name"] is None

    too_long = await client.post("/api/inboxes", json={"password": PASSWORD, "name": "x" * 81})
    assert too_long.status_code == 422
    assert "80" in too_long.json()["detail"]


async def test_short_password_is_rejected(client: httpx.AsyncClient):
    response = await client.post("/api/inboxes", json={"password": "short"})
    assert response.status_code == 422


async def test_unlock_with_password_returns_token(client: httpx.AsyncClient):
    session = await create_inbox(client)
    response = await client.post(f"/api/inboxes/{session['inbox']['id']}/session", json={"password": PASSWORD})
    assert response.status_code == 200
    assert response.json()["inbox"]["id"] == session["inbox"]["id"]


async def test_wrong_password_and_unknown_id_share_one_message(client: httpx.AsyncClient):
    session = await create_inbox(client)
    wrong = await client.post(
        f"/api/inboxes/{session['inbox']['id']}/session", json={"password": "not the password"}
    )
    unknown = await client.post(
        "/api/inboxes/00000000-0000-4000-8000-000000000000/session", json={"password": PASSWORD}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "Wrong inbox ID or password"}


async def test_session_attempts_are_rate_limited(make_settings):
    from app.main import create_app

    app = create_app(make_settings(session_attempts_per_minute=3))
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            session = await create_inbox(client)
            url = f"/api/inboxes/{session['inbox']['id']}/session"
            for _ in range(3):
                assert (await client.post(url, json={"password": "wrong-password"})).status_code == 401
            limited = await client.post(url, json={"password": PASSWORD})
            assert limited.status_code == 429
            assert int(limited.headers["retry-after"]) >= 1


async def test_session_attempts_are_limited_per_inbox_across_clients(make_settings):
    from app.main import create_app

    app = create_app(
        make_settings(
            session_attempts_per_minute=100,
            inbox_session_attempts_per_minute=3,
            trust_proxy_headers=True,
        )
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            session = await create_inbox(client)
            url = f"/api/inboxes/{session['inbox']['id']}/session"
            for i in range(3):
                headers = {"X-Forwarded-For": f"203.0.113.{i}"}
                resp = await client.post(url, json={"password": "wrong-password"}, headers=headers)
                assert resp.status_code == 401
            limited = await client.post(
                url, json={"password": PASSWORD}, headers={"X-Forwarded-For": "203.0.113.99"}
            )
            assert limited.status_code == 429


async def test_token_is_rejected_on_another_inbox(client: httpx.AsyncClient):
    first = await create_inbox(client, name="A")
    second = await create_inbox(client, name="B")

    other = await client.get(f"/api/inboxes/{second['inbox']['id']}", headers=auth(first))
    assert other.status_code == 403

    own = await client.get(f"/api/inboxes/{first['inbox']['id']}", headers=auth(first))
    assert own.status_code == 200
    assert own.json()["name"] == "A"


async def test_missing_or_bad_token_is_401(client: httpx.AsyncClient):
    session = await create_inbox(client)
    url = f"/api/inboxes/{session['inbox']['id']}"

    assert (await client.get(url)).status_code == 401
    assert (await client.get(url, headers={"Authorization": "Bearer not-a-jwt"})).status_code == 401
    assert (await client.get(url, headers={"Authorization": "Basic abc"})).status_code == 401


async def test_token_with_wrong_scope_is_401(client: httpx.AsyncClient, make_settings):
    import jwt

    session = await create_inbox(client)
    settings = make_settings()
    forged = jwt.encode(
        {"sub": session["inbox"]["id"], "scope": "ingest", "exp": 4102444800, "iat": 0},
        settings.secret_key,
        algorithm="HS256",
    )
    response = await client.get(
        f"/api/inboxes/{session['inbox']['id']}", headers={"Authorization": f"Bearer {forged}"}
    )
    assert response.status_code == 401


async def test_patch_renames_inbox(client: httpx.AsyncClient):
    session = await create_inbox(client, name="Old")
    response = await client.patch(
        f"/api/inboxes/{session['inbox']['id']}", json={"name": "New name"}, headers=auth(session)
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New name"

    cleared = await client.patch(
        f"/api/inboxes/{session['inbox']['id']}", json={"name": " "}, headers=auth(session)
    )
    assert cleared.json()["name"] is None


async def test_rotate_key_breaks_old_capture_url(client: httpx.AsyncClient):
    session = await create_inbox(client)
    old_key = session["inbox"]["ingest_key"]

    rotated = await client.post(f"/api/inboxes/{session['inbox']['id']}/rotate-key", headers=auth(session))
    assert rotated.status_code == 200
    new_key = rotated.json()["ingest_key"]
    assert new_key != old_key

    assert (await client.post(f"/api/hook/{old_key}", json={})).status_code == 404
    assert (await client.post(f"/api/hook/{new_key}", json={})).status_code == 200


async def test_delete_inbox_removes_it_and_its_capture_url(client: httpx.AsyncClient):
    session = await create_inbox(client)
    inbox_id = session["inbox"]["id"]
    key = session["inbox"]["ingest_key"]
    await client.post(f"/api/hook/{key}", json={"a": 1})

    deleted = await client.delete(f"/api/inboxes/{inbox_id}", headers=auth(session))
    assert deleted.status_code == 204

    assert (await client.get(f"/api/inboxes/{inbox_id}", headers=auth(session))).status_code == 404
    assert (await client.get(f"/api/inboxes/{inbox_id}/requests", headers=auth(session))).status_code == 404
    assert (await client.post(f"/api/hook/{key}", json={})).status_code == 404


async def test_removed_users_routes_are_gone(client: httpx.AsyncClient):
    assert (await client.post("/users/create", json={})).status_code == 404
    assert (await client.post("/resources/create", json={})).status_code == 404
    assert (await client.get("/")).status_code == 404


async def test_health(client: httpx.AsyncClient):
    response = await client.get("/api/health")
    assert response.json() == {"status": "ok"}
