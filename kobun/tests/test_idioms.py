"""慣用句エンドポイントのテスト。"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list(client: TestClient) -> None:
    r = client.get("/api/idioms")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 65
    assert {"idiom_id", "headword", "short_gloss"} <= body["items"][0].keys()


def test_detail(client: TestClient) -> None:
    first_id = client.get("/api/idioms").json()["items"][0]["idiom_id"]
    r = client.get(f"/api/idioms/{first_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["idiom_id"] == first_id
    assert body["headword"]


def test_detail_404(client: TestClient) -> None:
    assert client.get("/api/idioms/nope_0").status_code == 404
