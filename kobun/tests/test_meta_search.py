"""メタ・横断検索エンドポイントのテスト。"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_meta(client: TestClient) -> None:
    body = client.get("/api/meta").json()
    assert body["words"] == 315
    assert body["idioms"] == 65
    keys = {s["key"] for s in body["sections"]}
    assert {"part1", "part2", "keigo", "kanyouku"} == keys
    part1 = next(s for s in body["sections"] if s["key"] == "part1")
    assert part1["count"] == 163
    assert sum(p["count"] for p in part1["pos"]) == 163


def test_search(client: TestClient) -> None:
    body = client.get("/api/search", params={"q": "みる"}).json()
    assert "words" in body and "idioms" in body
    assert any(w["entry_no"] == "001" for w in body["words"])


def test_search_requires_q(client: TestClient) -> None:
    assert client.get("/api/search").status_code == 422


def test_healthz(client: TestClient) -> None:
    body = client.get("/healthz").json()
    assert body == {"status": "ok", "words": 315, "idioms": 65}
