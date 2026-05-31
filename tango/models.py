"""単語帳抽出結果の Pydantic スキーマ。

SPEC.md §3 のスキーマと完全に一致させる。
`Field(description=...)` は LLM 側 (Gemini の response_schema) にもヒントとして
伝播するため、説明文は SPEC 原文をそのまま保持する。
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class MeaningGroup(BaseModel):
    part_of_speech: str = Field(
        ...,
        description="品詞。例: '自動詞', '他動詞', '名詞', '形容詞' など",
    )
    meanings: List[str] = Field(
        ...,
        description=(
            "意味のリスト。①、②、③などの番号ごとに分解して配列に格納する。"
            "定義や補足説明がある場合はそれも含む"
        ),
    )


class WordOrigin(BaseModel):
    formula: Optional[str] = Field(
        None,
        description=(
            "語源のパーツ分解式。例: 'epi-[上] + -dem-[民衆] -> 「民衆の上に来る」'。"
            "存在しない場合はnull"
        ),
    )
    description: Optional[str] = Field(
        None,
        description=(
            "語源に関する派生語や補足説明。例: 'democracy「民主主義」, "
            "pandemic「全世界的な流行」'。存在しない場合はnull"
        ),
    )


class ExampleSentence(BaseModel):
    en: str = Field(..., description="例文の英語（またはフレーズ）")
    ja: str = Field(..., description="例文の日本語訳")


class VocabularyItem(BaseModel):
    id: str = Field(
        ...,
        description=(
            "単語番号。紙面にある3桁または4桁の数値（例: '001', '2090'）。"
            "完全に文字列として保持すること"
        ),
    )
    word: str = Field(..., description="見出し語（スペル）")
    phonetic: str = Field(..., description="発音記号。例: 'əgríː', 'èpədémik'")
    level_tag: Optional[str] = Field(
        None,
        description=(
            "重要度やレベルタグ。紙面にある 'A1', 'A2', '最難関' などの表記やラベル。"
            "無い場合はnull"
        ),
    )
    definitions: List[MeaningGroup] = Field(
        ...,
        description=(
            "品詞と意味のグループリスト。一つの単語に複数の品詞がある場合、"
            "それぞれ分けて格納する"
        ),
    )
    usages_and_notes: List[str] = Field(
        default_factory=list,
        description=(
            "[語法][注意][比較]などの枠内テキスト、派生語、コロケーション情報。"
            "無い場合は空配列"
        ),
    )
    word_origin: Optional[WordOrigin] = Field(
        None,
        description="語源情報。紙面に記述がない場合はnull",
    )
    examples: List[ExampleSentence] = Field(
        default_factory=list,
        description=(
            "例文とその訳のリスト。左右のページにまたがって対応するものや、"
            "解説枠内の簡易例文もペアにして格納。無い場合は空配列"
        ),
    )


class VocabularyExtractionResult(BaseModel):
    vocabulary_list: List[VocabularyItem]
