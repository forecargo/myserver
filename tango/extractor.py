"""Gemini Vision で単語帳画像から VocabularyExtractionResult を抽出する。

SPEC §3 のスキーマと §4 の抽出ルールに従い、Structured Output で取得する。
"""

from __future__ import annotations

import io
import logging
import re
from pathlib import Path
from typing import Optional

from google.genai import types
from PIL import Image, ImageOps

from config import MODEL_NAME, client
from models import VocabularyExtractionResult

logger = logging.getLogger(__name__)

# 画像長辺の上限 (品詞バッジなど小要素の可読性を確保)
MAX_IMAGE_SIDE = 3000

# meanings に紛れ込んだら usages_and_notes に移動する記号
NOTE_PREFIXES = ("▶", "▷", "★", "＊", "*", "◆", "■", "●")

# 単一POS+単一意味で勝手に付与された ① プレフィックスを剥がすための正規表現
_SOLO_NUMBER_RE = re.compile(r"^[①②③④⑤⑥⑦⑧⑨]\s*")

# Gemini に渡すシステム指示 (SPEC §4 の抽出ルールを反映)
SYSTEM_INSTRUCTION = """\
あなたは英語学習用の紙の単語帳ページをスキャンした画像を解析し、
構造化された JSON データに変換する熟練のデータ抽出エンジンです。

# 共通ルール
- ページ上部のヘッダー（例: 「意見・主張・提案」「最難関国公立・私大対策」）や、
  ページ下部のページ番号（例: 526, 527）は抽出対象から **除外** する。
- 英語フィールド（word / phonetic / examples.en）には英語のみ、
  日本語フィールド（meanings / usages_and_notes / examples.ja）には日本語のみを格納する。
  両者を混在させない。
- id は紙面の単語番号を **そのままの桁数で文字列として** 保持する（例: "001", "2090"）。
- 紙面に記述がない情報は null（任意）または空配列（リスト）にする。推測で値を埋めない。

# 品詞マーカー（最重要 — 誤分類を防ぐためのルール）
- 各見出し語のすぐ右には、品詞を示す **小さな青いバッジ** が並ぶ。
  バッジに含まれる文字は「**名**」「**形**」「**動**」「**副**」「**前**」「**接**」「**熟**」
  「**自**」「**他**」「**助**」「**冠**」など。これらをすべて検出対象とする。
- バッジが現れるたびに **必ず新しい definitions グループを開始** する。
  バッジを見逃すと、本来別品詞の意味が同じグループに混在し誤分類になる。
- 意味番号 ①②③④ は **品詞をまたいで連番** になっている場合がある
  （例: 名①「材料」②「資料」 形③「物質的な」④「重大な」）。
  「番号が連続している」ことを根拠に同じ品詞だと判断してはいけない。
  必ずバッジの位置で品詞境界を決定すること。
- バッジ位置の判定に迷ったら、意味の品詞性（名詞句か形容詞句か）を
  日本語訳から推定して整合性を確認する。

# 意味抽出の精度ルール（誤生成を防ぐ）
- **番号 ①②③ は紙面に明示されている場合のみ含める**。
  単一意味のエントリ（例: 名 能力 / 他 〜を達成する）に勝手に "①" を付けない。
  meanings = ["能力"], meanings = ["〜を達成する"] のように番号なしで格納する。
- **意味本体はバッジ直後の語句のみ**。コメント文や補足説明の中に出てくる
  括弧書きや修飾語を、意味本体に取り込まない。
  - 悪い例: 紙面が `名 能力 / 主に「(後天的な)能力」を示す最も一般的な語` のとき、
    meanings に "(後天的な)能力" と書く（コメント側の修飾語「(後天的な)」を取り込んでいる）
  - 良い例: meanings = ["能力"] / usages_and_notes に "主に「(後天的な)能力」を示す最も一般的な語"
- **見出し語ごとのエントリ境界を厳守**。
  各 VocabularyItem に含めるのは、その見出し語の直下〜次の見出し語の直前までの情報のみ。
  隣のエントリ（後続の見出し語）の意味・例文・派生語を流用しない。
  例: ability (#036) の definitions に talent (#037) の "才能" を混ぜない。

# 解説記号の扱い（meanings に混入させない — 最重要）
- **▶ ▷ ★ ＊ * ◆ ■ ●** などの記号で始まる行や、
  「**注意**」「**比較**」「**語法**」「**参考**」「**頻出**」「**派生**」「**類義**」「**反義**」
  などの枠ラベル付きテキストは、
  **その単語の語義（meaning）ではなく補足説明** である。必ず `usages_and_notes` に
  文字列として格納し、`meanings` には絶対に入れない。
- numbered meaning が **1個しかない場合でも**、その直下や横にある ▶ コメントは
  meanings には含めず、必ず `usages_and_notes` へ。
- 具体例:
  - 紙面: `他 ① 〜を達成する  ▶「苦労して(時間をかけて)ある基準にまで到達する」`
    → meanings = ["① 〜を達成する"], usages_and_notes に "▶「苦労して...」" を追加
  - 紙面: `名 ① 努力  ▶「努力」を示す最も一般的な語。`
    → meanings = ["① 努力"], usages_and_notes に "▶「努力」を示す..." を追加
- 反義語・派生語ブロック（例: `反 disagree「意見が合わない」`, `名 agreement「一致」`）も
  `usages_and_notes` に格納する。

# レイアウトA: 「重要な基本動詞」（例: look, see, watch, listen, hear, stand）
- 自他動詞マーク「自」「他」と意味番号 ① ② ③ を読み取り、
  definitions を part_of_speech（自動詞/他動詞）ごとに分けて meanings 配列に整理する。
- 「解説」「注意」「比較」枠の説明文（例: "Look at[×Look] that bird..."）は
  すべて usages_and_notes に **そのまま文字列として** 格納する。
- 紙面下部の [活用]（see-saw-seen 等）や、右側・解説枠内の短い例文表現
  （例: "I saw him."「彼を見た」）は可能な限り examples に { en, ja } ペアとして格納する。

# レイアウトB: 「意見・主張・提案」（例: agree, oppose, advise, tip, discuss）
- 左ページの見出し語と、右ページの対応する番号の英語例文・日本語訳を
  正しく結合し、当該 VocabularyItem の examples にマッピングする。
- 見出し語の左下にある "A1" "A2" 等のラベルは level_tag にマッピングする。

# レイアウトC: 「最難関国公立・私大対策」（例: epidemic, obesity, neuron）
- 青字で書かれた語源分解（例: "epi-[上] + -dem-[民衆] -> 「民衆の上に来る」"）は
  word_origin.formula に、その後に続く派生語・補足説明
  （例: 'democracy「民主主義」, pandemic「全世界的な流行」'）は word_origin.description に格納する。
- このレイアウトでは右ページに独立例文がない場合が多いため、
  見出し語下の解説中の短いフレーズや用例
  （例: "speed up your metabolism"「新陳代謝を高める」）は examples もしくは
  usages_and_notes として確実に拾う。

# 出力
- 紙面に存在するすべての見出し語を漏れなく抽出する。
- スキーマは VocabularyExtractionResult に厳密に従う。余計なフィールドを追加しない。
"""

USER_PROMPT = (
    "この画像は紙の英単語帳のスキャンページです。"
    "上記ルールに従って、すべての見出し語を VocabularyExtractionResult スキーマで抽出してください。"
)


def _load_image_bytes(
    image_path: Path,
    *,
    rotate_deg: int = 0,
) -> tuple[bytes, str]:
    """画像を読み込み、正立化・回転・縮小して JPEG bytes を返す。

    Args:
        image_path: 入力画像。
        rotate_deg: EXIF 補正後に追加で回す角度 (反時計回り 0/90/180/270)。
            ピクセルデータが右 90° 倒れているスキャンには 90 を指定する。
    """
    if rotate_deg not in (0, 90, 180, 270):
        raise ValueError(f"rotate_deg は 0/90/180/270 のいずれか: {rotate_deg}")

    with Image.open(image_path) as img:
        img.load()
        mime_type = "image/jpeg"
        # EXIF Orientation を反映して正立化 (スマホ撮影/スキャナの横向きデータ対策)
        img = ImageOps.exif_transpose(img)
        # EXIF が嘘をついている場合の救済 (手動指定の追加回転)
        if rotate_deg:
            img = img.rotate(rotate_deg, expand=True)
        # RGBA / P モードは JPEG 化のため RGB に変換
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        longest = max(img.size)
        if longest > MAX_IMAGE_SIDE:
            scale = MAX_IMAGE_SIDE / longest
            original_size = img.size
            new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
            img = img.resize(new_size, Image.LANCZOS)
            logger.info("resized %s: %s -> %s", image_path.name, original_size, new_size)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92, optimize=True)
        return buf.getvalue(), mime_type


def _strip_solo_number_prefix(result: VocabularyExtractionResult) -> None:
    """単一POSグループ+単一意味で勝手に付いた "① " プレフィックスを剥がす。

    複数POSグループに各1意味ある場合（例: 他①/自②）の連番は仕様通りなので残す。
    複数意味がある場合の番号も残す。条件を厳しく絞ることで誤剥離を防ぐ。
    """
    for item in result.vocabulary_list:
        if len(item.definitions) != 1:
            continue
        d = item.definitions[0]
        if len(d.meanings) != 1:
            continue
        m = d.meanings[0]
        stripped = _SOLO_NUMBER_RE.sub("", m.lstrip())
        if stripped != m:
            d.meanings[0] = stripped


def _move_notes_out_of_meanings(result: VocabularyExtractionResult) -> None:
    """meanings に紛れ込んだ ▶▷★＊ などの補足コメントを usages_and_notes へ移す。

    LLM がたまに ▶ で始まる中核説明を meaning として返すことがあるため、
    決定論的に矯正する。
    """
    for item in result.vocabulary_list:
        moved: list[str] = []
        for d in item.definitions:
            kept: list[str] = []
            for m in d.meanings:
                if m.lstrip().startswith(NOTE_PREFIXES):
                    moved.append(m)
                else:
                    kept.append(m)
            d.meanings = kept
        if moved:
            # 重複は避けつつ先頭側に挿入 (元の文脈に近い位置)
            existing = set(item.usages_and_notes)
            new_items = [m for m in moved if m not in existing]
            item.usages_and_notes = new_items + item.usages_and_notes


def extract_from_image(
    image_path: Path,
    *,
    model_name: Optional[str] = None,
    temperature: float = 0.1,
    rotate_deg: int = 0,
) -> VocabularyExtractionResult:
    """単一画像を Gemini に流し込み、抽出結果を返す。

    Args:
        image_path: 単語帳ページのスキャン画像。
        model_name: 使用する Gemini モデル名。None なら config.MODEL_NAME を使用。
        temperature: 生成温度。抽出タスクなので低めに設定。
        rotate_deg: EXIF 補正後に追加で回す角度 (反時計回り 0/90/180/270)。

    Returns:
        VocabularyExtractionResult: スキーマ準拠の抽出結果。
    """
    image_bytes, mime_type = _load_image_bytes(image_path, rotate_deg=rotate_deg)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=temperature,
        response_mime_type="application/json",
        response_schema=VocabularyExtractionResult,
    )

    response = client.models.generate_content(
        model=model_name or MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            USER_PROMPT,
        ],
        config=config,
    )

    # SDK が response_schema を解釈して parsed に Pydantic オブジェクトを返す
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, VocabularyExtractionResult):
        result = parsed
    else:
        # フォールバック: text を Pydantic で再バリデート
        text = response.text or ""
        if not text:
            raise RuntimeError(
                f"Gemini が空のレスポンスを返しました: {image_path.name}"
            )
        result = VocabularyExtractionResult.model_validate_json(text)

    _move_notes_out_of_meanings(result)
    _strip_solo_number_prefix(result)
    return result
