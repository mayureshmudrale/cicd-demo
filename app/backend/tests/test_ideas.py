import pytest
from fastapi.testclient import TestClient

from config import settings
from main import app


def test_healthz(client: TestClient) -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_list_idea(client: TestClient) -> None:
    created = client.post("/ideas", json={"text": "ship phase 2"})
    assert created.status_code == 201
    assert created.json()["votes"] == 0

    listed = client.get("/ideas")
    assert listed.status_code == 200
    assert any(idea["text"] == "ship phase 2" for idea in listed.json())


def test_upvote(client: TestClient) -> None:
    created = client.post("/ideas", json={"text": "upvote me"}).json()
    upvoted = client.post(f"/ideas/{created['id']}/upvote")
    assert upvoted.status_code == 200
    assert upvoted.json()["votes"] == 1


def test_upvote_missing_returns_404(client: TestClient) -> None:
    resp = client.post("/ideas/999999/upvote")
    assert resp.status_code == 404


def test_fault_error500(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "fault_mode", "error500")
    resp = client.get("/ideas")
    assert resp.status_code == 500


def test_fault_panic_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "fault_mode", "panic")
    with TestClient(app, raise_server_exceptions=False) as unsafe_client:
        resp = unsafe_client.get("/ideas")
    assert resp.status_code == 500
