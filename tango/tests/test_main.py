"""main.py CLI のうち API を呼ばないヘルパのテスト。

Gemini 呼び出しを伴う extract_from_image をモンキーパッチで差し替えて、
process_image のフロー (skip / ok / error) と find_images のフィルタを検証する。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

import main
from models import (
    MeaningGroup,
    VocabularyExtractionResult,
    VocabularyItem,
)


def _make_jpeg(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (200, 200), color="white").save(path, format="JPEG")


def _stub_result() -> VocabularyExtractionResult:
    return VocabularyExtractionResult(
        vocabulary_list=[
            VocabularyItem(
                id="001",
                word="hello",
                phonetic="həlóu",
                definitions=[
                    MeaningGroup(part_of_speech="間投詞", meanings=["こんにちは"])
                ],
            )
        ]
    )


# ---------- find_images ----------

def test_find_images_picks_supported_extensions(tmp_path: Path):
    _make_jpeg(tmp_path / "a.jpg")
    _make_jpeg(tmp_path / "b.JPEG")
    _make_jpeg(tmp_path / "c.png")
    _make_jpeg(tmp_path / "d.webp")
    (tmp_path / "skip.txt").write_text("nope", encoding="utf-8")
    (tmp_path / "skip.pdf").write_bytes(b"%PDF-1.4")

    images = main.find_images(tmp_path)
    assert [p.name for p in images] == ["a.jpg", "b.JPEG", "c.png", "d.webp"]


def test_find_images_raises_when_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        main.find_images(tmp_path / "does_not_exist")


# ---------- process_image ----------

def test_process_image_writes_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    src = tmp_path / "in" / "img.jpg"
    out_dir = tmp_path / "out"
    _make_jpeg(src)

    monkeypatch.setattr(main, "extract_from_image", lambda p, **kw: _stub_result())
    out_dir.mkdir()

    status = main.process_image(src, out_dir, overwrite=False)
    assert status == "ok"

    written = out_dir / "img.json"
    assert written.exists()
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["vocabulary_list"][0]["word"] == "hello"
    # ensure_ascii=False で日本語が生のまま保存されている
    assert "こんにちは" in written.read_text(encoding="utf-8")


def test_process_image_skips_existing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    src = tmp_path / "img.jpg"
    out_dir = tmp_path
    _make_jpeg(src)
    (out_dir / "img.json").write_text("{}", encoding="utf-8")

    called = {"n": 0}

    def fake_extract(_: Path, **_kw) -> VocabularyExtractionResult:
        called["n"] += 1
        return _stub_result()

    monkeypatch.setattr(main, "extract_from_image", fake_extract)

    status = main.process_image(src, out_dir, overwrite=False)
    assert status == "skip"
    assert called["n"] == 0  # API は呼ばれない


def test_process_image_overwrite_invokes_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    src = tmp_path / "img.jpg"
    out_dir = tmp_path
    _make_jpeg(src)
    (out_dir / "img.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(main, "extract_from_image", lambda p, **kw: _stub_result())

    status = main.process_image(src, out_dir, overwrite=True)
    assert status == "ok"
    payload = json.loads((out_dir / "img.json").read_text(encoding="utf-8"))
    assert payload["vocabulary_list"][0]["word"] == "hello"


def test_process_image_returns_error_on_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    src = tmp_path / "img.jpg"
    out_dir = tmp_path
    _make_jpeg(src)

    def boom(_: Path, **_kw) -> VocabularyExtractionResult:
        raise RuntimeError("network down")

    monkeypatch.setattr(main, "extract_from_image", boom)

    status = main.process_image(src, out_dir, overwrite=False)
    assert status == "error"
    assert not (out_dir / "img.json").exists()  # 失敗時はファイルを作らない
