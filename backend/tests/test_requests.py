import httpx

from tests.conftest import auth, create_inbox


async def _seed(client: httpx.AsyncClient, session: dict, bodies: list[str]) -> list[int]:
    key = session["inbox"]["ingest_key"]
    ids = []
    for body in bodies:
        response = await client.post(f"/api/hook/{key}", content=body.encode(), headers={"Content-Type": "text/plain"})
        ids.append(response.json()["id"])
    return ids


async def test_list_is_newest_first_with_cursor_pagination(client: httpx.AsyncClient):
    session = await create_inbox(client)
    ids = await _seed(client, session, ["one", "two", "three", "four", "five"])
    url = f"/api/inboxes/{session['inbox']['id']}/requests"

    first = (await client.get(f"{url}?limit=2", headers=auth(session))).json()
    assert [item["id"] for item in first["items"]] == [ids[4], ids[3]]
    assert first["has_more"] is True

    second = (await client.get(f"{url}?limit=2&before_id={first['items'][-1]['id']}", headers=auth(session))).json()
    assert [item["id"] for item in second["items"]] == [ids[2], ids[1]]
    assert second["has_more"] is True

    last = (await client.get(f"{url}?limit=2&before_id={second['items'][-1]['id']}", headers=auth(session))).json()
    assert [item["id"] for item in last["items"]] == [ids[0]]
    assert last["has_more"] is False

    inbox = (await client.get(f"/api/inboxes/{session['inbox']['id']}", headers=auth(session))).json()
    assert inbox["request_count"] == 5


async def test_limit_out_of_range_is_422(client: httpx.AsyncClient):
    session = await create_inbox(client)
    url = f"/api/inboxes/{session['inbox']['id']}/requests"
    assert (await client.get(f"{url}?limit=0", headers=auth(session))).status_code == 422
    assert (await client.get(f"{url}?limit=201", headers=auth(session))).status_code == 422


async def test_method_filter(client: httpx.AsyncClient):
    session = await create_inbox(client)
    key = session["inbox"]["ingest_key"]
    await client.get(f"/api/hook/{key}")
    await client.post(f"/api/hook/{key}", json={})
    await client.post(f"/api/hook/{key}", json={})

    page = (
        await client.get(f"/api/inboxes/{session['inbox']['id']}/requests?method=post", headers=auth(session))
    ).json()
    assert len(page["items"]) == 2
    assert {item["method"] for item in page["items"]} == {"POST"}


async def test_search_matches_path_body_and_headers_case_insensitively(client: httpx.AsyncClient):
    session = await create_inbox(client)
    key = session["inbox"]["ingest_key"]
    url = f"/api/inboxes/{session['inbox']['id']}/requests"
    by_path = (await client.get(f"/api/hook/{key}/Orders/42")).json()["id"]
    by_body = (await client.post(f"/api/hook/{key}", content=b"payment=APPROVED")).json()["id"]
    by_header = (
        await client.post(f"/api/hook/{key}", content=b"x", headers={"X-Tenant": "acme-corp"})
    ).json()["id"]

    async def search(q: str) -> list[int]:
        response = await client.get(url, params={"q": q}, headers=auth(session))
        assert response.status_code == 200
        return [item["id"] for item in response.json()["items"]]

    assert await search("orders/42") == [by_path]
    assert await search("approved") == [by_body]
    assert await search("ACME-corp") == [by_header]


async def test_search_treats_percent_and_underscore_literally(client: httpx.AsyncClient):
    session = await create_inbox(client)
    key = session["inbox"]["ingest_key"]
    url = f"/api/inboxes/{session['inbox']['id']}/requests"
    await client.post(f"/api/hook/{key}", content=b"discount 100% off")
    await client.post(f"/api/hook/{key}", content=b"discount 1000 off")
    await client.post(f"/api/hook/{key}", content=b"snake_case_name")
    await client.post(f"/api/hook/{key}", content=b"snakeXcaseXname")

    percent = (await client.get(url, params={"q": "100%"}, headers=auth(session))).json()
    assert [item["body"] for item in percent["items"]] == ["discount 100% off"]

    underscore = (await client.get(url, params={"q": "snake_case"}, headers=auth(session))).json()
    assert [item["body"] for item in underscore["items"]] == ["snake_case_name"]


async def test_get_request_from_another_inbox_is_404(client: httpx.AsyncClient):
    mine = await create_inbox(client, name="mine")
    theirs = await create_inbox(client, name="theirs")
    [their_id] = await _seed(client, theirs, ["secret"])

    response = await client.get(
        f"/api/inboxes/{mine['inbox']['id']}/requests/{their_id}", headers=auth(mine)
    )
    assert response.status_code == 404

    missing = await client.get(f"/api/inboxes/{mine['inbox']['id']}/requests/999999", headers=auth(mine))
    assert missing.status_code == 404


async def test_delete_one_request(client: httpx.AsyncClient):
    session = await create_inbox(client)
    url = f"/api/inboxes/{session['inbox']['id']}/requests"
    keep, drop = await _seed(client, session, ["keep", "drop"])

    deleted = await client.delete(f"{url}/{drop}", headers=auth(session))
    assert deleted.status_code == 204
    assert (await client.get(f"{url}/{drop}", headers=auth(session))).status_code == 404
    assert (await client.delete(f"{url}/{drop}", headers=auth(session))).status_code == 404

    remaining = (await client.get(url, headers=auth(session))).json()["items"]
    assert [item["id"] for item in remaining] == [keep]


async def test_clear_all_requests(client: httpx.AsyncClient):
    session = await create_inbox(client)
    url = f"/api/inboxes/{session['inbox']['id']}/requests"
    await _seed(client, session, ["a", "b", "c"])

    cleared = await client.delete(url, headers=auth(session))
    assert cleared.status_code == 204
    page = (await client.get(url, headers=auth(session))).json()
    assert page == {"items": [], "has_more": False}


async def test_pruning_keeps_only_the_newest(make_settings):
    from app.main import create_app
    from tests.conftest import create_inbox as make_inbox

    app = create_app(make_settings(max_requests_per_inbox=3))
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            session = await make_inbox(client)
            ids = await _seed(client, session, ["1", "2", "3", "4", "5"])
            page = (
                await client.get(f"/api/inboxes/{session['inbox']['id']}/requests", headers=auth(session))
            ).json()
            assert [item["id"] for item in page["items"]] == ids[-3:][::-1]
            assert page["has_more"] is False


async def test_export_is_a_json_attachment(client: httpx.AsyncClient):
    session = await create_inbox(client)
    ids = await _seed(client, session, ["first", "second"])

    response = await client.get(f"/api/inboxes/{session['inbox']['id']}/export", headers=auth(session))
    assert response.status_code == 200
    assert response.headers["content-disposition"] == f'attachment; filename="inbox-{session["inbox"]["id"]}.json"'
    assert [item["id"] for item in response.json()] == [ids[1], ids[0]]


async def test_stale_token_after_inbox_delete_is_404_not_500(client: httpx.AsyncClient):
    session = await create_inbox(client)
    await client.delete(f"/api/inboxes/{session['inbox']['id']}", headers=auth(session))
    response = await client.get(f"/api/inboxes/{session['inbox']['id']}/requests", headers=auth(session))
    assert response.status_code == 404
