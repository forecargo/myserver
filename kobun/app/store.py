"""`assets/data/` を起動時にメモリ展開し、検索・クイズ・索引を提供する読み取り専用ストア。

データは静的・小規模（単語 315・慣用句 65）なので DB は使わず、すべてメモリ上で完結する。
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path

from . import config
from .models import (
    IdiomDetail,
    IdiomListItem,
    MetaResponse,
    PosCount,
    QuizChoice,
    QuizPrompt,
    QuizQuestion,
    QuizResponse,
    SectionMeta,
    WordDetail,
    WordListItem,
)

logger = logging.getLogger(__name__)

_GLOSS_SEP = "／"
_LIST_GLOSS_LIMIT = 2  # 一覧 short_gloss に載せる語義数の上限


def _short_gloss(glosses: list[str]) -> str:
    """語義リストを一覧用の短い説明に連結する。"""
    return _GLOSS_SEP.join(g for g in glosses[:_LIST_GLOSS_LIMIT] if g)


def _mistake_note_is_empty(note: dict | None) -> bool:
    """誤用注意がすべて空かどうか。"""
    if not note:
        return True
    return not any((note.get("wrong"), note.get("correct"), note.get("note")))


@dataclass
class _WordRecord:
    """単語 1 件分の内部レコード（詳細・一覧・検索/クイズ補助を保持）。"""

    detail: WordDetail
    list_item: WordListItem
    search_text: str
    primary_gloss: str


@dataclass
class _IdiomRecord:
    """慣用句 1 件分の内部レコード。"""

    detail: IdiomDetail
    list_item: IdiomListItem
    search_text: str


@dataclass
class Store:
    """ロード済みデータと索引を保持するインメモリストア。"""

    words: dict[str, _WordRecord] = field(default_factory=dict)
    word_order: list[str] = field(default_factory=list)  # entry_no を昇順保持
    idioms: dict[str, _IdiomRecord] = field(default_factory=dict)
    idiom_order: list[str] = field(default_factory=list)
    # 品詞 → 語義候補（クイズのダミー選択肢サンプリング用）
    _glosses_by_pos: dict[str, list[str]] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # ロード
    # ------------------------------------------------------------------ #
    @classmethod
    def load(cls, data_dir: Path | None = None) -> Store:
        """`assets/data/` 配下の JSON を全件読み込んでストアを構築する。

        Args:
            data_dir: データディレクトリ。未指定なら ``config.DATA_DIR``。

        Returns:
            構築済みの :class:`Store`。
        """
        base = data_dir or config.DATA_DIR
        store = cls()

        for section in config.WORD_SECTIONS:
            for path in sorted((base / section).glob("*.json")):
                store._load_word_file(path, section)

        for path in sorted((base / config.IDIOM_SECTION).glob("*.json")):
            store._load_idiom_file(path)

        store.word_order.sort(key=lambda no: (len(no), no))
        store._build_quiz_pool()
        logger.info("loaded kobun data: %d words, %d idioms", len(store.words), len(store.idioms))
        return store

    def _load_word_file(self, path: Path, section: str) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        pos_category = data.get("pos_category")
        for raw in data.get("entries", []):
            self._add_word(raw, section, pos_category)

    def _add_word(self, raw: dict, section: str, pos_category: str | None) -> None:
        entry_no = raw["entry_no"]
        meanings = raw.get("meanings", []) or []
        glosses = [m.get("gloss", "") for m in meanings]
        image_url = config.build_image_url((raw.get("manga") or {}).get("image_path"))

        detail = WordDetail(
            entry_no=entry_no,
            section=section,
            pos_category=pos_category,
            headword=raw.get("headword", ""),
            reading=raw.get("reading") or None,
            image_url=image_url,
            headword_variants=raw.get("headword_variants", []) or [],
            sub_glosses=raw.get("sub_glosses", []) or [],
            conjugation_type=raw.get("conjugation_type") or None,
            meanings=meanings,
            word_formation=raw.get("word_formation") or None,
            semantic_shift=raw.get("semantic_shift") or None,
            honorific=raw.get("honorific") or None,
            related_words=raw.get("related_words", []) or [],
            commentary=raw.get("commentary") or None,
            examples=raw.get("examples", []) or [],
            mistake_note=(
                None if _mistake_note_is_empty(raw.get("mistake_note")) else raw["mistake_note"]
            ),
            tip_box=raw.get("tip_box") or None,
            qr_code=raw.get("qr_code"),
            pages=raw.get("pages", []) or [],
        )
        list_item = WordListItem(
            entry_no=entry_no,
            section=section,
            pos_category=pos_category,
            headword=detail.headword,
            reading=detail.reading,
            image_url=image_url,
            short_gloss=_short_gloss(glosses),
        )
        search_parts = [
            detail.headword,
            detail.reading or "",
            *detail.headword_variants,
            *detail.sub_glosses,
            *glosses,
        ]
        self.words[entry_no] = _WordRecord(
            detail=detail,
            list_item=list_item,
            search_text=" ".join(search_parts).casefold(),
            primary_gloss=glosses[0] if glosses else detail.headword,
        )
        self.word_order.append(entry_no)

    def _load_idiom_file(self, path: Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        stem = path.stem  # 例: kobun-kanyouku-10
        for index, raw in enumerate(data.get("idioms", [])):
            self._add_idiom(raw, stem, index, data.get("printed_page"))

    def _add_idiom(self, raw: dict, stem: str, index: int, printed_page: int | None) -> None:
        idiom_id = f"{stem}_{index}"  # 画像ファイル名と一致する安定 ID
        senses = raw.get("senses", []) or []
        top_meanings = raw.get("meanings", []) or []
        if senses:
            glosses = [m.get("gloss", "") for s in senses for m in (s.get("meanings") or [])]
            writings = [s.get("writing", "") for s in senses if s.get("writing")]
        else:
            glosses = [m.get("gloss", "") for m in top_meanings]
            writings = []
        image_url = config.build_image_url((raw.get("manga") or {}).get("image_path"))

        detail = IdiomDetail(
            idiom_id=idiom_id,
            headword=raw.get("headword", ""),
            reading=raw.get("reading") or None,
            image_url=image_url,
            meanings=top_meanings,
            senses=senses,
            commentary=raw.get("commentary") or None,
            examples=raw.get("examples", []) or [],
            related=raw.get("related", []) or [],
            printed_page=printed_page,
        )
        list_item = IdiomListItem(
            idiom_id=idiom_id,
            headword=detail.headword,
            reading=detail.reading,
            image_url=image_url,
            short_gloss=_short_gloss(glosses),
        )
        search_parts = [detail.headword, detail.reading or "", *writings, *glosses]
        self.idioms[idiom_id] = _IdiomRecord(
            detail=detail,
            list_item=list_item,
            search_text=" ".join(search_parts).casefold(),
        )
        self.idiom_order.append(idiom_id)

    def _build_quiz_pool(self) -> None:
        pool: dict[str, list[str]] = {}
        for rec in self.words.values():
            pool.setdefault(rec.detail.pos_category or "", []).append(rec.primary_gloss)
        self._glosses_by_pos = pool

    # ------------------------------------------------------------------ #
    # 単語クエリ
    # ------------------------------------------------------------------ #
    def get_word(self, entry_no: str) -> WordDetail | None:
        rec = self.words.get(entry_no)
        return rec.detail if rec else None

    def list_words(
        self,
        *,
        section: str | None = None,
        pos: str | None = None,
        q: str | None = None,
        ids: list[str] | None = None,
    ) -> list[WordListItem]:
        """条件に合致する単語の一覧項目を ``entry_no`` 昇順で返す。"""
        if ids is not None:
            # 指定順を保ち、存在するものだけ返す（暗記・復習の集合取得用）。
            return [self.words[i].list_item for i in ids if i in self.words]

        needle = q.casefold() if q else None
        result: list[WordListItem] = []
        for entry_no in self.word_order:
            rec = self.words[entry_no]
            if section and rec.detail.section != section:
                continue
            if pos and rec.detail.pos_category != pos:
                continue
            if needle and needle not in rec.search_text:
                continue
            result.append(rec.list_item)
        return result

    # ------------------------------------------------------------------ #
    # 慣用句クエリ
    # ------------------------------------------------------------------ #
    def get_idiom(self, idiom_id: str) -> IdiomDetail | None:
        rec = self.idioms.get(idiom_id)
        return rec.detail if rec else None

    def list_idioms(
        self, *, q: str | None = None, ids: list[str] | None = None
    ) -> list[IdiomListItem]:
        """条件に合致する慣用句の一覧項目を返す。"""
        if ids is not None:
            return [self.idioms[i].list_item for i in ids if i in self.idioms]

        needle = q.casefold() if q else None
        result: list[IdiomListItem] = []
        for idiom_id in self.idiom_order:
            rec = self.idioms[idiom_id]
            if needle and needle not in rec.search_text:
                continue
            result.append(rec.list_item)
        return result

    # ------------------------------------------------------------------ #
    # メタ
    # ------------------------------------------------------------------ #
    def meta(self) -> MetaResponse:
        """区分・件数・品詞内訳を返す。"""
        sections: list[SectionMeta] = []
        for key in config.WORD_SECTIONS:
            items = [r for r in self.words.values() if r.detail.section == key]
            pos_counts: dict[str, int] = {}
            for r in items:
                pos_counts[r.detail.pos_category or "不明"] = (
                    pos_counts.get(r.detail.pos_category or "不明", 0) + 1
                )
            sections.append(
                SectionMeta(
                    key=key,
                    label=config.SECTION_LABELS.get(key, key),
                    type="words",
                    count=len(items),
                    pos=[PosCount(key=k, count=v) for k, v in pos_counts.items()],
                )
            )
        sections.append(
            SectionMeta(
                key=config.IDIOM_SECTION,
                label=config.SECTION_LABELS.get(config.IDIOM_SECTION, config.IDIOM_SECTION),
                type="idioms",
                count=len(self.idioms),
            )
        )
        return MetaResponse(words=len(self.words), idioms=len(self.idioms), sections=sections)

    # ------------------------------------------------------------------ #
    # クイズ
    # ------------------------------------------------------------------ #
    def quiz(
        self,
        *,
        section: str | None = None,
        pos: str | None = None,
        count: int = 10,
        choices: int = 4,
        rng: random.Random | None = None,
    ) -> QuizResponse:
        """見出し語の意味を当てる 4 択問題を生成する。

        ダミー選択肢は同品詞の他語の意味を優先してサンプリングし、正解と重複しないようにする。
        """
        rng = rng or random.Random()
        candidates = [
            self.words[no]
            for no in self.word_order
            if (not section or self.words[no].detail.section == section)
            and (not pos or self.words[no].detail.pos_category == pos)
        ]
        n = min(count, len(candidates))
        targets = rng.sample(candidates, n) if n else []

        questions: list[QuizQuestion] = []
        for i, rec in enumerate(targets):
            distractors = self._sample_distractors(rec, choices - 1, rng)
            options = [rec.primary_gloss, *distractors]
            rng.shuffle(options)
            answer_index = options.index(rec.primary_gloss)
            questions.append(
                QuizQuestion(
                    question_id=f"{rec.detail.entry_no}-{i}",
                    entry_no=rec.detail.entry_no,
                    pos_category=rec.detail.pos_category,
                    prompt=QuizPrompt(headword=rec.detail.headword, reading=rec.detail.reading),
                    choices=[QuizChoice(index=j, gloss=g) for j, g in enumerate(options)],
                    answer_index=answer_index,
                )
            )
        return QuizResponse(count=len(questions), questions=questions)

    def _sample_distractors(self, rec: _WordRecord, want: int, rng: random.Random) -> list[str]:
        """正解と重複しないダミー選択肢を ``want`` 件返す（同品詞優先）。"""
        correct = rec.primary_gloss
        pos = rec.detail.pos_category or ""
        same_pos = [g for g in self._glosses_by_pos.get(pos, []) if g != correct]
        others = [
            g
            for key, glosses in self._glosses_by_pos.items()
            if key != pos
            for g in glosses
            if g != correct
        ]
        rng.shuffle(same_pos)
        rng.shuffle(others)

        picked: list[str] = []
        seen = {correct}
        for g in [*same_pos, *others]:
            if g in seen:
                continue
            picked.append(g)
            seen.add(g)
            if len(picked) >= want:
                break
        return picked
