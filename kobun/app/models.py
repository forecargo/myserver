"""API レスポンスの Pydantic v2 モデル。

`assets/data/` の JSON スキーマ（CLAUDE.md「データスキーマ（参照仕様）」）を元に定義する。
全フィールド optional 前提・欠落省略のため、レスポンスは ``exclude_none`` で配信する。
"""

from __future__ import annotations

from pydantic import BaseModel

# --------------------------------------------------------------------------- #
# 共通
# --------------------------------------------------------------------------- #


class Meaning(BaseModel):
    """丸囲み数字の語義。"""

    no: int | None = None
    gloss: str


# --------------------------------------------------------------------------- #
# 単語（part1 / part2 / keigo）
# --------------------------------------------------------------------------- #


class Example(BaseModel):
    """例文（古文原文と現代語訳の対）。"""

    sense_no: int | None = None
    marker: str | None = None
    text: str
    target_words: list[str] = []
    translation: str | None = None
    source: str | None = None


class RelatedWord(BaseModel):
    """関連語（関 / 同 / 反）。"""

    marker: str | None = None
    word: str = ""
    reading: str = ""
    meanings: list[Meaning] = []


class Honorific(BaseModel):
    """敬語の種別と原義。"""

    type: str
    base_word: str | None = None


class SemanticShift(BaseModel):
    """古/現の意味対比。"""

    modern: str | None = None
    classical: str | None = None


class MistakeNote(BaseModel):
    """誤用注意（×/○）。"""

    wrong: str = ""
    correct: str = ""
    note: str = ""


class WordBase(BaseModel):
    """単語の共通項目。"""

    entry_no: str
    section: str
    pos_category: str | None = None
    headword: str
    reading: str | None = None
    image_url: str | None = None


class WordListItem(WordBase):
    """一覧用の軽量項目。"""

    short_gloss: str


class WordDetail(WordBase):
    """単語詳細。"""

    headword_variants: list[str] = []
    sub_glosses: list[str] = []
    conjugation_type: str | None = None
    meanings: list[Meaning] = []
    word_formation: str | None = None
    semantic_shift: SemanticShift | None = None
    honorific: Honorific | None = None
    related_words: list[RelatedWord] = []
    commentary: str | None = None
    examples: list[Example] = []
    mistake_note: MistakeNote | None = None
    tip_box: str | None = None
    qr_code: bool | None = None
    pages: list[int] = []


# --------------------------------------------------------------------------- #
# 慣用句（kanyouku）
# --------------------------------------------------------------------------- #


class IdiomSense(BaseModel):
    """同形異義のまとまり（A / B）。"""

    label: str | None = None
    writing: str | None = None
    meanings: list[Meaning] = []


class IdiomExample(BaseModel):
    """慣用句の例文。"""

    sense_label: str | None = None
    marker: str | None = None
    text: str
    target_words: list[str] = []
    translation: str | None = None
    source: str | None = None


class IdiomRelated(BaseModel):
    """関連語・関連慣用句。"""

    marker: str | None = None
    word: str = ""
    reading: str = ""
    meanings: list[Meaning] = []


class IdiomBase(BaseModel):
    """慣用句の共通項目。"""

    idiom_id: str
    headword: str
    reading: str | None = None
    image_url: str | None = None


class IdiomListItem(IdiomBase):
    """一覧用の軽量項目。"""

    short_gloss: str


class IdiomDetail(IdiomBase):
    """慣用句詳細。``senses`` が無い場合は ``meanings`` を直下に持つ。"""

    meanings: list[Meaning] = []
    senses: list[IdiomSense] = []
    commentary: str | None = None
    examples: list[IdiomExample] = []
    related: list[IdiomRelated] = []
    printed_page: int | None = None


# --------------------------------------------------------------------------- #
# 一覧レスポンス（ページング）
# --------------------------------------------------------------------------- #


class WordListResponse(BaseModel):
    """`/api/words` のレスポンス。"""

    total: int
    limit: int | None = None
    offset: int = 0
    items: list[WordListItem]


class IdiomListResponse(BaseModel):
    """`/api/idioms` のレスポンス。"""

    total: int
    limit: int | None = None
    offset: int = 0
    items: list[IdiomListItem]


class SearchResponse(BaseModel):
    """`/api/search` のレスポンス（単語・慣用句の横断）。"""

    words: list[WordListItem]
    idioms: list[IdiomListItem]


# --------------------------------------------------------------------------- #
# メタ
# --------------------------------------------------------------------------- #


class PosCount(BaseModel):
    """区分内の品詞別件数。"""

    key: str
    count: int


class SectionMeta(BaseModel):
    """区分（章）のメタ情報。"""

    key: str
    label: str
    type: str  # "words" | "idioms"
    count: int
    pos: list[PosCount] = []


class MetaResponse(BaseModel):
    """`/api/meta` のレスポンス。"""

    words: int
    idioms: int
    sections: list[SectionMeta]


# --------------------------------------------------------------------------- #
# クイズ
# --------------------------------------------------------------------------- #


class QuizPrompt(BaseModel):
    """出題語（見出し語・読み）。"""

    headword: str
    reading: str | None = None


class QuizChoice(BaseModel):
    """選択肢。"""

    index: int
    gloss: str


class QuizQuestion(BaseModel):
    """4 択問題 1 問。採点は端末側（``answer_index`` 同梱）。"""

    question_id: str
    entry_no: str
    pos_category: str | None = None
    prompt: QuizPrompt
    choices: list[QuizChoice]
    answer_index: int


class QuizResponse(BaseModel):
    """`/api/quiz` のレスポンス。"""

    count: int
    questions: list[QuizQuestion]


# --------------------------------------------------------------------------- #
# ヘルス
# --------------------------------------------------------------------------- #


class HealthResponse(BaseModel):
    """`/healthz` のレスポンス。"""

    status: str
    words: int
    idioms: int
