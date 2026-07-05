"""クイズエンドポイントのテスト。"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_quiz_shape(client: TestClient) -> None:
    body = client.get("/api/quiz", params={"count": 10, "choices": 4}).json()
    assert body["count"] == 10
    assert len(body["questions"]) == 10
    for q in body["questions"]:
        assert len(q["choices"]) == 4
        assert 0 <= q["answer_index"] < 4
        # 正解の選択肢が answer_index に一致する。
        correct = q["choices"][q["answer_index"]]["gloss"]
        glosses = [c["gloss"] for c in q["choices"]]
        assert glosses.count(correct) == 1  # 選択肢に重複なし


def test_quiz_filtered_by_pos(client: TestClient) -> None:
    body = client.get("/api/quiz", params={"pos": "形容詞", "count": 5}).json()
    assert all(q["pos_category"] == "形容詞" for q in body["questions"])


def test_quiz_count_capped_to_pool(client: TestClient) -> None:
    # keigo は 26 件。count を超えても件数はプール上限まで。
    body = client.get("/api/quiz", params={"section": "keigo", "count": 50}).json()
    assert body["count"] == 26
