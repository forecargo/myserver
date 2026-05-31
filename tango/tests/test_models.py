"""Pydantic スキーマ (models.py) のバリデーションテスト。

SPEC §3 のスキーマ契約を恒久的に守るための機械検証。
template_layoute.json と既存 output/*.json も同じスキーマで往復できることを確認する。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from models import (
    ExampleSentence,
    MeaningGroup,
    VocabularyExtractionResult,
    VocabularyItem,
    WordOrigin,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "template_layoute.json"
OUTPUT_DIR = PROJECT_ROOT / "output"


# ---------- スキーマ往復 (SPEC §3 契約) ----------

def test_template_layoute_roundtrip():
    """SPEC が示すテンプレ JSON が現スキーマでパース・再シリアライズできる。"""
    data = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    result = VocabularyExtractionResult(**data)
    assert len(result.vocabulary_list) == 2

    # 値の整合 (代表項目)
    agree = result.vocabulary_list[0]
    assert agree.id == "001"
    assert agree.word == "agree"
    assert agree.level_tag == "A1"
    assert len(agree.definitions) == 2
    assert {d.part_of_speech for d in agree.definitions} == {"自動詞", "他動詞"}
    assert len(agree.examples) == 2
    assert agree.word_origin is not None

    # epidemic は examples が空配列 (default_factory=list が機能)
    epidemic = result.vocabulary_list[1]
    assert epidemic.id == "2090"
    assert epidemic.examples == []
    assert epidemic.usages_and_notes == []
    assert epidemic.word_origin.formula.startswith("epi-")


def test_template_roundtrip_dict_equivalent():
    """model_dump() がテンプレ JSON と意味的に等価 (キー集合・値) になる。"""
    data = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    result = VocabularyExtractionResult(**data)
    redumped = result.model_dump()
    assert redumped == data


# ---------- 必須/省略可フィールドの境界 ----------

def test_optional_fields_default_to_none_and_empty_list():
    item = VocabularyItem(
        id="999",
        word="dummy",
        phonetic="dʌ́mi",
        definitions=[MeaningGroup(part_of_speech="名詞", meanings=["仮値"])],
    )
    assert item.level_tag is None
    assert item.word_origin is None
    assert item.usages_and_notes == []
    assert item.examples == []


def test_missing_required_field_raises():
    """definitions が無いと ValidationError になる (SPEC: 必須)。"""
    with pytest.raises(ValidationError):
        VocabularyItem(id="000", word="x", phonetic="x")


def test_id_must_be_string_to_preserve_padding():
    """id は文字列フィールド: 整数を渡すと文字列強制 or 警告される (SPEC: 桁数保持)。"""
    item = VocabularyItem(
        id="001",
        word="x",
        phonetic="x",
        definitions=[MeaningGroup(part_of_speech="名詞", meanings=["y"])],
    )
    assert item.id == "001"
    assert isinstance(item.id, str)


def test_example_sentence_requires_both_languages():
    with pytest.raises(ValidationError):
        ExampleSentence(en="hello")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        ExampleSentence(ja="やあ")  # type: ignore[call-arg]


def test_word_origin_both_fields_optional():
    wo = WordOrigin()
    assert wo.formula is None
    assert wo.description is None


# ---------- 既存 output/*.json を回帰スイートとして検証 ----------

OUTPUT_JSON_FILES = sorted(OUTPUT_DIR.glob("*.json")) if OUTPUT_DIR.is_dir() else []


@pytest.mark.skipif(not OUTPUT_JSON_FILES, reason="output/*.json が未生成")
@pytest.mark.parametrize("path", OUTPUT_JSON_FILES, ids=lambda p: p.name)
def test_output_files_match_schema(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    result = VocabularyExtractionResult(**data)
    assert len(result.vocabulary_list) > 0
    for item in result.vocabulary_list:
        assert item.id and isinstance(item.id, str)
        assert item.word
        assert item.phonetic
        assert len(item.definitions) >= 1
