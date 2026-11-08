import json

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import create_app
from tests.conftest import PASSWORD, ORIGIN

def _setup(make_settings):
    app = create_app(make_settings())
    return app


def test_auth_then_ready_then_request_created(make_settings):
    with TestClient(_setup(make_settings)) as client:
        session = client.post("/api/inboxes", json={"password": PASSWORD}).json()
        inbox_id = session["inbox"]["id"]
        with client.websocket_connect(f"/api/inboxes/{inbox_id}/stream", headers={"origin": ORIGIN}) as ws:
            ws.send_json({"type": "auth", "token": session["access_token"]})
            assert ws.receive_json() == {"type": "ready"}

            posted = client.post(f"/api/hook/{session['inbox']['ingest_key']}/live", json={"n": 1}).json()
            event = ws.receive_json()

    assert event["type"] == "request.created"
    assert event["data"]["id"] == posted["id"]
    assert event["data"]["path"] == "/live"
    assert json.loads(event["data"]["body"]) == {"n": 1}


def test_bad_token_closes_4401(make_settings):
    with TestClient(_setup(make_settings)) as client:
        session = client.post("/api/inboxes", json={"password": PASSWORD}).json()
        with client.websocket_connect(f"/api/inboxes/{session['inbox']['id']}/stream") as ws:
            ws.send_json({"type": "auth", "token": "garbage"})
            with pytest.raises(WebSocketDisconnect) as excinfo:
                ws.receive_json()
    assert excinfo.value.code == 4401


def test_token_for_another_inbox_closes_4401(make_settings):
    with TestClient(_setup(make_settings)) as client:
        first = client.post("/api/inboxes", json={"password": PASSWORD}).json()
        second = client.post("/api/inboxes", json={"password": PASSWORD}).json()
        with client.websocket_connect(f"/api/inboxes/{second['inbox']['id']}/stream") as ws:
            ws.send_json({"type": "auth", "token": first["access_token"]})
            with pytest.raises(WebSocketDisconnect) as excinfo:
                ws.receive_json()
    assert excinfo.value.code == 4401


def test_token_in_query_string_is_not_accepted(make_settings):
    with TestClient(_setup(make_settings)) as client:
        session = client.post("/api/inboxes", json={"password": PASSWORD}).json()
        url = f"/api/inboxes/{session['inbox']['id']}/stream?token={session['access_token']}"
        with client.websocket_connect(url) as ws:
            ws.send_json({"type": "ping"})
            with pytest.raises(WebSocketDisconnect) as excinfo:
                ws.receive_json()
    assert excinfo.value.code == 4401


def test_disallowed_origin_is_rejected_4403(make_settings):
    with TestClient(_setup(make_settings)) as client:
        session = client.post("/api/inboxes", json={"password": PASSWORD}).json()
        url = f"/api/inboxes/{session['inbox']['id']}/stream"
        with pytest.raises(WebSocketDisconnect) as excinfo:
            with client.websocket_connect(url, headers={"origin": "https://evil.example"}):
                pass
    assert excinfo.value.code == 4403


def test_client_messages_are_not_echoed(make_settings):
    with TestClient(_setup(make_settings)) as client:
        session = client.post("/api/inboxes", json={"password": PASSWORD}).json()
        inbox_id = session["inbox"]["id"]
        with client.websocket_connect(f"/api/inboxes/{inbox_id}/stream") as ws:
            ws.send_json({"type": "auth", "token": session["access_token"]})
            assert ws.receive_json() == {"type": "ready"}
            ws.send_text("hello from the client")
            # A capture after the chatter proves nothing was echoed in between.
            client.post(f"/api/hook/{session['inbox']['ingest_key']}", json={"after": True})
            event = ws.receive_json()
    assert event["type"] == "request.created"


def test_deleting_inbox_sends_event_then_closes_4404(make_settings):
    with TestClient(_setup(make_settings)) as client:
        session = client.post("/api/inboxes", json={"password": PASSWORD}).json()
        inbox_id = session["inbox"]["id"]
        headers = {"Authorization": f"Bearer {session['access_token']}"}
        with client.websocket_connect(f"/api/inboxes/{inbox_id}/stream") as ws:
            ws.send_json({"type": "auth", "token": session["access_token"]})
            assert ws.receive_json() == {"type": "ready"}
            assert client.delete(f"/api/inboxes/{inbox_id}", headers=headers).status_code == 204
            assert ws.receive_json() == {"type": "inbox.deleted"}
            with pytest.raises(WebSocketDisconnect) as excinfo:
                ws.receive_json()
    assert excinfo.value.code == 4404


def test_auth_timeout_closes_4401(make_settings, monkeypatch):
    import app.routers.stream as stream

    monkeypatch.setattr(stream, "AUTH_TIMEOUT_SECONDS", 0.2)
    with TestClient(_setup(make_settings)) as client:
        session = client.post("/api/inboxes", json={"password": PASSWORD}).json()
        with client.websocket_connect(f"/api/inboxes/{session['inbox']['id']}/stream") as ws:
            with pytest.raises(WebSocketDisconnect) as excinfo:
                ws.receive_json()
    assert excinfo.value.code == 4401
