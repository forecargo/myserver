"""extractor.py のうち API を呼ばない純粋ロジックのテスト。

Gemini への HTTP 呼び出しはコスト・速度の都合でテストしない。
画像前処理 (_load_image_bytes) のリサイズ判定とフォーマット変換のみカバーする。
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from extractor import (
    MAX_IMAGE_SIDE,
    _load_image_bytes,
    _move_notes_out_of_meanings,
    _strip_solo_number_prefix,
)
from models import (
    MeaningGroup,
    VocabularyExtractionResult,
    VocabularyItem,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = PROJECT_ROOT / "sample_jpg"


def _decode(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes))


def test_resize_when_longer_than_max(tmp_path: Path):
    """長辺が MAX_IMAGE_SIDE を超える画像はその上限に縮小される。"""
    src = tmp_path / "big.jpg"
    Image.new("RGB", (4000, 3000), color="white").save(src, format="JPEG")

    out_bytes, mime = _load_image_bytes(src)
    assert mime == "image/jpeg"

    out_img = _decode(out_bytes)
    assert max(out_img.size) == MAX_IMAGE_SIDE
    # アスペクト比保持 (誤差 ±1px)
    assert abs(out_img.size[0] / out_img.size[1] - 4000 / 3000) < 0.01


def test_no_resize_when_within_max(tmp_path: Path):
    """長辺が MAX_IMAGE_SIDE 以下なら元サイズを保つ。"""
    src = tmp_path / "small.jpg"
    Image.new("RGB", (1024, 768), color="white").save(src, format="JPEG")

    out_bytes, _ = _load_image_bytes(src)
    out_img = _decode(out_bytes)
    assert out_img.size == (1024, 768)


def test_rgba_input_is_converted_to_rgb(tmp_path: Path):
    """RGBA PNG を渡しても JPEG として保存できる (RGB に変換される)。"""
    src = tmp_path / "rgba.png"
    Image.new("RGBA", (800, 600), color=(255, 0, 0, 128)).save(src, format="PNG")

    out_bytes, mime = _load_image_bytes(src)
    assert mime == "image/jpeg"
    out_img = _decode(out_bytes)
    assert out_img.mode == "RGB"
    assert out_img.size == (800, 600)


@pytest.mark.skipif(
    not (SAMPLE_DIR.is_dir() and any(SAMPLE_DIR.iterdir())),
    reason="sample_jpg/ が存在しない",
)
def test_real_sample_image_is_normalized():
    """実サンプル画像 (高解像度スキャン) も上限内に正規化される。"""
    samples = sorted(SAMPLE_DIR.glob("*.jpg"))
    assert samples, "sample_jpg/*.jpg が見つかりません"
    out_bytes, _ = _load_image_bytes(samples[0])
    out_img = _decode(out_bytes)
    assert max(out_img.size) <= MAX_IMAGE_SIDE


def test_manual_rotate_90_swaps_dimensions(tmp_path: Path):
    """rotate_deg=90 (CCW) で 1000x600 → 600x1000 に入れ替わる。"""
    src = tmp_path / "tilt.jpg"
    Image.new("RGB", (1000, 600), color="white").save(src, format="JPEG")
    out_bytes, _ = _load_image_bytes(src, rotate_deg=90)
    out_img = _decode(out_bytes)
    assert out_img.size == (600, 1000)


def test_invalid_rotate_deg_raises(tmp_path: Path):
    src = tmp_path / "any.jpg"
    Image.new("RGB", (100, 100), color="white").save(src, format="JPEG")
    with pytest.raises(ValueError):
        _load_image_bytes(src, rotate_deg=45)


def test_exif_orientation_is_applied(tmp_path: Path):
    """EXIF Orientation=8 (左 90 度回転で正立) が付いた画像が正立化される。

    1000x600 の横長ピクセルデータに Orientation=8 を埋め込んで保存すると、
    exif_transpose で正しく解釈すれば 600x1000 (縦長) に補正される。
    """
    src = tmp_path / "rotated.jpg"
    img = Image.new("RGB", (1000, 600), color="white")
    exif = img.getexif()
    exif[0x0112] = 8  # Orientation
    img.save(src, format="JPEG", exif=exif)

    out_bytes, _ = _load_image_bytes(src)
    out_img = _decode(out_bytes)
    assert out_img.size == (600, 1000)


# ---------- 後処理: ▶ コメントの meanings 流出を矯正 ----------

def _make_item(definitions, usages=None):
    return VocabularyItem(
        id="001",
        word="x",
        phonetic="x",
        definitions=definitions,
        usages_and_notes=usages or [],
    )


def test_move_notes_extracts_arrow_prefixes():
    result = VocabularyExtractionResult(
        vocabulary_list=[
            _make_item([
                MeaningGroup(
                    part_of_speech="他",
                    meanings=["① 〜を達成する", "▶「苦労してある基準まで到達する」"],
                )
            ])
        ]
    )
    _move_notes_out_of_meanings(result)
    item = result.vocabulary_list[0]
    assert item.definitions[0].meanings == ["① 〜を達成する"]
    assert item.usages_and_notes == ["▶「苦労してある基準まで到達する」"]


# ---------- 後処理: 単一POS+単一意味の① 剥がし ----------

def test_strip_solo_number_removes_prefix():
    """単一POS+単一意味+①付きは番号を剥がす。"""
    result = VocabularyExtractionResult(
        vocabulary_list=[
            _make_item([MeaningGroup(part_of_speech="名", meanings=["① 政府"])])
        ]
    )
    _strip_solo_number_prefix(result)
    assert result.vocabulary_list[0].definitions[0].meanings == ["政府"]


def test_strip_solo_number_keeps_multi_meaning_numbers():
    """複数意味の番号は剥がさない。"""
    result = VocabularyExtractionResult(
        vocabulary_list=[
            _make_item([
                MeaningGroup(part_of_speech="名", meanings=["① 練習", "② 実践"])
            ])
        ]
    )
    _strip_solo_number_prefix(result)
    assert result.vocabulary_list[0].definitions[0].meanings == ["① 練習", "② 実践"]


def test_strip_solo_number_keeps_cross_pos_numbering():
    """複数POSグループにそれぞれ1意味 (番号は ①② 連番) は剥がさない。"""
    result = VocabularyExtractionResult(
        vocabulary_list=[
            _make_item([
                MeaningGroup(part_of_speech="他動詞", meanings=["① 〜と主張する"]),
                MeaningGroup(part_of_speech="自動詞", meanings=["② 〜と言い争う"]),
            ])
        ]
    )
    _strip_solo_number_prefix(result)
    assert result.vocabulary_list[0].definitions[0].meanings == ["① 〜と主張する"]
    assert result.vocabulary_list[0].definitions[1].meanings == ["② 〜と言い争う"]


def test_strip_solo_number_handles_unicode_circle_digits():
    """単一POS+単一意味の各番号文字 (①〜⑨) を網羅。"""
    for circled in "①②③④⑤⑥⑦⑧⑨":
        result = VocabularyExtractionResult(
            vocabulary_list=[
                _make_item([
                    MeaningGroup(part_of_speech="名", meanings=[f"{circled} 意味"])
                ])
            ]
        )
        _strip_solo_number_prefix(result)
        assert result.vocabulary_list[0].definitions[0].meanings == ["意味"]
