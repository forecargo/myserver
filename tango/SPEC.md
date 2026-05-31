SPECIFICATION: 単語帳画像データ抽出プログラムの開発 (Vocab Extractor)

1. プロジェクト概要 (Overview)

本プロジェクトは、娘向けのオリジナル単語帳アプリ開発の第一段階として、紙の単語帳のスキャン画像（JPEG/PNG等）から、学習用データを構造化されたJSON形式で高精度に自動抽出するプログラムを構築することを目的とします。

処理には、画像認識と自然言語理解に優れたVision-LLM（例：Google Gemini 2.5 Flash または OpenAI GPT-4o）を使用し、紙面のレイアウト差を吸収して共通のデータスキーマに落とし込みます。

2. 動作環境・技術スタック (Technology Stack)

開発言語: Python 3.10+

利用ライブラリ候補:

google-genai (Gemini API) または openai (OpenAI API) ※画像認識性能、コスト、速度の面から選択。

pydantic (JSONスキーマ定義およびバリデーション)

Pillow (画像処理・サイズ調整)

python-dotenv (環境変数・APIキー管理)

動作フロー:

指定された入力ディレクトリから画像を読み込む

画像をLLMのVision APIに流し込み、定義されたPydanticスキーマに沿ったJSONデータの生成を要求する（Structured Outputsの利用）

出力されたJSONデータをバリデーションし、保存ディレクトリに単語ごとに、またはページごとに保存する

3. データ構造定義 (Data Structure Definition)

LLMに厳密なフォーマットで出力させるため、およびアプリ側で扱いやすくするために、以下のPydanticクラスで定義されるJSONスキーマを標準とします。

from typing import List, Optional
from pydantic import BaseModel, Field

class MeaningGroup(BaseModel):
    part_of_speech: str = Field(
        ..., 
        description="品詞。例: '自動詞', '他動詞', '名詞', '形容詞' など"
    )
    meanings: List[str] = Field(
        ..., 
        description="意味のリスト。①、②、③などの番号ごとに分解して配列に格納する。定義や補足説明がある場合はそれも含む"
    )

class WordOrigin(BaseModel):
    formula: Optional[str] = Field(
        None, 
        description="語源のパーツ分解式。例: 'epi-[上] + -dem-[民衆] -> 「民衆の上に来る」'。存在しない場合はnull"
    )
    description: Optional[str] = Field(
        None, 
        description="語源に関する派生語や補足説明。例: 'democracy「民主主義」, pandemic「全世界的な流行」'。存在しない場合はnull"
    )

class ExampleSentence(BaseModel):
    en: str = Field(..., description="例文の英語（またはフレーズ）")
    ja: str = Field(..., description="例文の日本語訳")

class VocabularyItem(BaseModel):
    id: str = Field(
        ..., 
        description="単語番号。紙面にある3桁または4桁の数値（例: '001', '2090'）。完全に文字列として保持すること"
    )
    word: str = Field(..., description="見出し語（スペル）")
    phonetic: str = Field(..., description="発音記号。例: 'əgríː', 'èpədémik'")
    level_tag: Optional[str] = Field(
        None, 
        description="重要度やレベルタグ。紙面にある 'A1', 'A2', '最難関' などの表記やラベル。無い場合はnull"
    )
    definitions: List[MeaningGroup] = Field(
        ..., 
        description="品詞と意味のグループリスト。一つの単語に複数の品詞がある場合、それぞれ分けて格納する"
    )
    usages_and_notes: List[str] = Field(
        default_factory=list, 
        description="[語法][注意][比較]などの枠内テキスト、派生語、コロケーション情報。無い場合は空配列"
    )
    word_origin: Optional[WordOrigin] = Field(
        None, 
        description="語源情報。紙面に記述がない場合はnull"
    )
    examples: List[ExampleSentence] = Field(
        default_factory=list, 
        description="例文とその訳のリスト。左右のページにまたがって対応するものや、解説枠内の簡易例文もペアにして格納。無い場合は空配列"
    )

class VocabularyExtractionResult(BaseModel):
    vocabulary_list: List[VocabularyItem]


4. 抽出ルールとマッピング指針 (Extraction Guidelines)

プログラム内のプロンプト、あるいはLLM呼び出しロジックは以下のルールを遵守する必要があります。

A. 3つのレイアウト共通ルール

紙面ノイズの除去: ページ上部のヘッダー（「意見・主張・提案」「最難関国公立・私大対策」など）や、ページ下部のページ番号（526, 527など）は抽出対象外とする。

テキストのクレンジング: テキストに含まれる記号（矢印 ▶, ▷, *, ★ など）は、意味を損なわない範囲で適宜クレンジングするか、一貫性を持った文字列として抽出する。

B. レイアウト別抽出ルール

「重要な基本動詞」レイアウト（例: look, see, watch, listen, hear, stand）

品詞と意味の対応: 「自 ①(at～)を見る」「他 ④(熟語で)～をじっと見つめる」のように、自他動詞マーク（「自」「他」）と番号（①②③）があるため、definitions 内で part_of_speech（自動詞/他動詞）ごとに meanings（配列）を綺麗に分解・整理すること。

解説・比較の抽出: 「解説」「注意」「比較」に書かれている説明文（例: Look at[×Look] that bird...）は、すべて usages_and_notes 配列に文字列として格納すること。

例文の紐付け: 紙面下部の [活用]（see-saw-seen等）や、右側あるいは解説枠内にある短い例文表現（I saw him.「彼を見た」）は、可能な限り英語・日本語を抽出して examples に格納する。

「意見・主張・提案」レイアウト（例: agree, oppose, advise, tip, discuss）

左右ページの統合: 左ページの見出し語と、右ページにある対応する番号の「例文（英語）」「例文訳（日本語）」を正しく結合し、該当する単語オブジェクトの examples にマッピングすること。

シンボル・ラベル: 見出し語の左下にある A1, A2 などのラベルを level_tag にマッピングすること。

「最難関国公立・私大対策」レイアウト（例: epidemic, obesity, neuron）

語源のパース: 青文字で書かれている語源分解（例: epi-[上]+-dem-[民衆] -> 「民衆の上に来る」）を word_origin.formula に、その後に続く説明（例: democracy「民主主義」...）を word_origin.description にきれいに格納すること。

例文の有無: このレイアウトでは右ページに独立した例文がない場合が多いため、見出し語の下の解説に書かれている短いフレーズや用例（例: speed up your metabolism 「新代謝を高める」）を examples もしくは usages_and_notes として抽出する。

5. Claude Code への開発タスク指示 (Tasks for Claude Code)

Claude Codeは、以下のステップに沿って段階的に実装を行ってください。

タスク 1: 環境構築と設定

[x] requirements.txt の作成

必要なパッケージ (pydantic, pillow, google-genai もしくは openai, python-dotenv) を記述。

[x] .env.template の作成

GEMINI_API_KEY または OPENAI_API_KEY を設定するためのテンプレートファイル。

[x] APIクライアント初期化モジュール (config.py) の実装。

タスク 2: データ構造（Pydanticモデル）の実装

[x] models.py の作成

本仕様書「3. データ構造定義」の Pydantic モデルを正確に定義。

タスク 3: LLM連携・データ抽出エンジンの実装

[x] extractor.py の作成

画像ファイルのパスを受け取り、LLMのVisionモデルを呼び出す関数を実装。

重要な要件: LLMの Structured Outputs 機能（Geminiの response_schema や OpenAIの response_format）を利用し、出力が必ず VocabularyExtractionResult のスキーマに沿った valid な JSON になるように設計すること。

プロンプトテンプレートを定義。プロンプト内で「3つのレイアウトの特徴」と「抽出マッピングルール」を英語または日本語で詳細に指示すること。

タスク 4: 複数画像バッチ処理とファイル保存スクリプトの実装

[x] main.py の作成

コマンドラインから実行可能にする。

入力画像ディレクトリ内の全画像をループ処理し、抽出結果を `data/<batch>/<画像名>.json` として保存する仕組み。

エラーハンドリング（API接続エラー、不完全なJSONのパースエラー）を組み込み、処理が途中で落ちてもそれまでに抽出したデータを保護する。

タスク 5: テストと動作確認

[x] テストスクリプトの作成、または単一画像でのテスト実行。

[x] 出力された JSON がスキーマに合致しているか、日本語の文字化け（Unicodeエスケープ形式ではなく生文字で出力されているか）などを確認・修正する。

6. 出力ファイルの検証基準 (Acceptance Criteria)

抽出処理の結果、得られるJSONファイルは以下の条件を全て満たさなければならない。

スキーマ妥当性: pydantic の検証に100%パスすること。

言語の整合性: 英語（word, phonetic, examples.en）と日本語（meanings, usages_and_notes, examples.ja）が正しく各フィールドにマッピングされ、混ざっていないこと。

データ欠落の最小化: 紙面上の主要な意味や例文が、OCRエラーやLLMの無視によって欠落していないこと。

7. ディレクトリ構成・ファイル命名規約 (Directory Layout)

```
tango/
├── config.py / models.py / extractor.py / main.py / viewer.py
├── requirements.txt / requirements-dev.txt / .env.template
├── SPEC.md / CLAUDE.md / template_layoute.json
├── sample_jpg/         # テスト基準データ (3枚, pytest が依存)
├── output/             # テスト回帰用 JSON 基準 (3件, pytest が依存)
├── scans/              # 本番スキャン画像 (.gitignore 対象)
│   └── <batch>/        # 例: part1/, part2/
├── data/               # 抽出済み JSON (git 管理)
│   └── <batch>/
└── tests/              # pytest スイート
```

**ファイル命名規約**: `<book> - <batch> - <NN>.<ext>` (NN は 2桁ゼロパディング、01 起点)

- 例: `LEAP - part1 - 01.jpg` ↔ `LEAP - part1 - 01.json`
- 自然順ソートを保証し、batch スコープと連番を同時に表現する

**Git 管理方針**:

- `scans/` は著作物のため除外 (`.gitignore` で `/scans/` を指定)
- `data/` は履歴管理対象 (再抽出コスト保護のため)
- `.env` は親リポジトリ `/Users/nobuhiro/Python/myserver/.env` を共用 (`config.py` が `Path(__file__).parent.parent / ".env"` をロード)

8. 画像前処理仕様 (Image Preprocessing)

`extractor._load_image_bytes()` は Gemini に渡す前に以下を順に適用する。

1. **EXIF Orientation 補正**: `PIL.ImageOps.exif_transpose()` でカメラ/スキャナの自動回転メタデータを反映
2. **手動回転 (オプション)**: `--rotate {0,90,180,270}` (反時計回り角度)。EXIF が嘘 (Orientation=1 だがピクセルが横倒し) のスキャンを救済
3. **モード変換**: RGBA / P → RGB (JPEG 化のため)
4. **リサイズ**: 長辺 `MAX_IMAGE_SIDE=2048` を超える場合は LANCZOS で縮小 (API コスト最適化)
5. **JPEG エンコード**: quality=92, optimize=True

回転状態がバッチ内で混在しないようにし、`--rotate` 値はバッチ単位で固定するのが運用前提。

9. 確認 UI 仕様 (viewer.py)

`http://127.0.0.1:8765/` で起動するローカル FastAPI アプリ。

| エンドポイント | 用途 |
| --- | --- |
| `GET /` | SPA (シングルページ HTML) |
| `GET /api/batches` | `data/` 配下のバッチ名一覧 |
| `GET /api/files/{batch}` | バッチ内の `{stem, count, has_image}` 一覧 |
| `GET /api/data/{batch}/{stem}` | 抽出 JSON をそのまま返す |
| `GET /image/{batch}/{stem}` | scans/ 配下の元画像を EXIF + 90° 回転で正立化して返す |

UI 機能:
- 左ペインに正立画像、右ペインに `VocabularyItem` カード一覧 (id/word/phonetic/level、品詞別の意味、語法・注意、語源、例文)
- サイドバーにバッチ選択、ファイル名と抽出件数 (バッジ)、前後ナビ
- キーボード ← → でページ送り、アクティブ項目は自動スクロール追従

10. 実装モジュール構成 (Module Layout)

| モジュール | 責務 |
| --- | --- |
| `config.py` | 親 `.env` ロード、Gemini クライアント初期化、`MODEL_NAME` / `INPUT_DIR` / `OUTPUT_DIR` 定数 |
| `models.py` | §3 の Pydantic スキーマ (5 クラス) |
| `extractor.py` | 画像前処理 + Gemini Vision 呼び出し (`response_schema=VocabularyExtractionResult` で Structured Output) |
| `main.py` | argparse による CLI バッチ処理。画像単位 try/except でエラー隔離、既出力スキップ (`--overwrite` で強制再抽出) |
| `viewer.py` | §9 の FastAPI 確認 UI |
| `tests/` | pytest スイート (API は呼ばないモック化テスト) |

**LLM 選定**: Google Gemini 2.5 Flash (`google-genai>=2.7`)。Structured Output を `response_schema=VocabularyExtractionResult` で直接利用し、SDK が Pydantic オブジェクトを `response.parsed` に返す挙動に依拠する。

11. テスト戦略 (Testing)

`tests/` 配下に pytest スイートを配置。**Gemini API は呼ばない** (コスト・速度の都合)。

| ファイル | カバー範囲 |
| --- | --- |
| `tests/test_models.py` | §3 スキーマ契約: `template_layoute.json` 往復、必須/省略可フィールド境界、`id` 文字列保持、`output/*.json` の回帰検証 |
| `tests/test_extractor.py` | 画像前処理: リサイズ判定、RGBA→RGB 変換、EXIF Orientation 補正、`--rotate` の境界値 |
| `tests/test_main.py` | CLI ヘルパ: `find_images` の拡張子フィルタ、`process_image` の ok/skip/overwrite/error 経路 (`extract_from_image` を monkeypatch) |

実行: `.venv/bin/python -m pytest tests/ -q`