"""単語エンドポイントのテスト。"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_all(client: TestClient) -> None:
    r = client.get("/api/words")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 315
    assert len(body["items"]) == 315
    assert {"entry_no", "headword", "section", "short_gloss"} <= body["items"][0].keys()


def test_filter_section_and_pos(client: TestClient) -> None:
    r = client.get("/api/words", params={"section": "part1", "pos": "動詞"})
    body = r.json()
    assert body["total"] > 0
    assert all(i["section"] == "part1" and i["pos_category"] == "動詞" for i in body["items"])


def test_pagination(client: TestClient) -> None:
    r = client.get("/api/words", params={"limit": 5, "offset": 10})
    body = r.json()
    assert body["total"] == 315
    assert len(body["items"]) == 5
    assert body["items"][0]["entry_no"] == "011"


def test_search_query(client: TestClient) -> None:
    r = client.get("/api/words", params={"q": "みる"})
    body = r.json()
    assert any(i["entry_no"] == "001" for i in body["items"])


def test_ids_preserves_order(client: TestClient) -> None:
    r = client.get("/api/words", params={"ids": "005,001,012"})
    body = r.json()
    assert [i["entry_no"] for i in body["items"]] == ["005", "001", "012"]


def test_detail(client: TestClient) -> None:
    r = client.get("/api/words/001")
    assert r.status_code == 200
    body = r.json()
    assert body["headword"] == "見る"
    assert body["conjugation_type"] == "マ行上一段"
    assert len(body["meanings"]) >= 1
    assert body["image_url"] == "/assets/manga/part1/001.png"


def test_detail_excludes_none(client: TestClient) -> None:
    # 001 は honorific が無いので exclude_none でキー自体が落ちる。
    body = client.get("/api/words/001").json()
    assert "honorific" not in body


def test_detail_404(client: TestClient) -> None:
    assert client.get("/api/words/999").status_code == 404
