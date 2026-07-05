# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクトの目的

古文単語アプリ（iOS クライアント等）へ**単語・慣用句データと暗記カード画像を配信する API サーバ**を構築・運用するプロジェクト。

データ化フェーズは**完了済み**で、成果物は `assets/` 配下に確定済みデータ（JSON）と暗記カード画像（PNG）として格納されている。本プロジェクトの現在のゴールは、この静的データをアプリから利用しやすい形で提供する **FastAPI ベースの API サーバ**を作ることである。

- **データは静的・確定済み**。API はこれを読み取り専用で提供する。データの再生成・編集は原則行わない（誤り発見時は `assets/data/` の JSON を直接修正する）。
- API サーバ実装の置き場所、ディレクトリ構成は「ディレクトリ構成」節を参照。

> データ化フェーズの経緯・誌面レイアウトの読み取り方法・OCR 手順などは本ドキュメントの対象外（完了済み）。スキーマ定義のみ「データスキーマ（参照仕様）」節に **API レスポンスの元仕様**として保持する。

***

## 配信対象データ（`assets/`）

データ化の成果物。**API はこれを唯一のデータソースとして読み込む**。

### 構成

```
assets/
├── data/                       # 確定済み JSON（211 ファイル）
│   ├── part1/   kobun-*.json            # 第1章（見出し 001〜163, 101 ファイル）
│   ├── part2/   kobun-Part2-*.json      # 第2章（見出し 164〜289, 73 ファイル）
│   ├── keigo/   kobun-keigo-*.json      # 敬語（見出し 290〜315, 18 ファイル）
│   └── kanyouku/ kobun-kanyouku-*.json  # 慣用句（番号なし, 19 ファイル）
└── manga/                      # 暗記カード画像（380 PNG, 各 1024×1024）
    ├── part1/   001.png 〜 163.png       # 見出し番号 = ファイル名
    ├── part2/   164.png 〜 289.png
    ├── keigo/   290.png 〜 315.png
    └── kanyouku/ kobun-kanyouku-N_M.png  # ファイル名_連番
```

### データ量（実測・検証済み）

| 区分 | 識別子 | エントリ数 | 画像 |
|---|---|---|---|
| part1 | 見出し番号 001〜163 | 163 | 163 |
| part2 | 見出し番号 164〜289 | 126 | 126 |
| keigo | 見出し番号 290〜315 | 26 | 26 |
| kanyouku | 見出し語（番号なし） | 65 慣用句 | 65 |

- 単語エントリ合計 **315 件**（見出し番号 001〜315、**欠番・重複なし**）。慣用句 **65 件**。
- `pos_category` 内訳: 動詞 67・形容詞 80・名詞 68・副詞 47・形容動詞 27・敬語 26。
- 全エントリの `manga.image_path` は実在を確認済み（**欠落・孤立画像ともゼロ**）。`manga.status` は全件 `generated`。

### 識別子ルール（API のキー設計）

- **単語（part1/part2/keigo）**: `entry_no`（3桁ゼロ埋め文字列 `"001"`〜`"315"`）が**全区分通しの一意キー**。API の単語リソースの主キーに使う。
- **区分（section）**: `entry_no` のレンジで決まる（001-163=part1 / 164-289=part2 / 290-315=keigo）。`pos_category` は JSON 内に保持。
- **慣用句（kanyouku）**: 見出し番号を持たない。安定 ID として **`{JSON ファイル名（拡張子なし）}_{ファイル内 index}`**（例 `kobun-kanyouku-10_0`）を用いる。画像ファイル名と一致するため画像参照と整合する。

***

## 技術スタック / 開発環境

- **言語**: Python 3.12（`.python-version` で pin、`requires-python = ">=3.12"`）。型ヒント必須、docstring は Google スタイル。
- **フレームワーク**: **FastAPI**（兄弟サービス `ocr-api` / `guidline-api` / `trouble-api` と統一。`uvicorn` で起動、`pydantic` v2 でモデル定義）。
- **仮想環境・パッケージ管理**: `uv`。`conda` は使わない。dev 依存に `ruff`・`pytest`（+ `httpx` で API テスト）。
- **データ保持方式**: **起動時に `assets/data/**/*.json` を全件読み込み、Pydantic モデルへ正規化してメモリ上に保持**（静的・小規模のためDB不要）。検索・フィルタもメモリ上で完結させる。
- **画像配信**: **静的ファイル配信**。FastAPI `StaticFiles`（開発）または Caddy `file_server`（本番）で `assets/manga/` を公開し、API レスポンスは画像 URL/パスのみ返す。

### よく使うコマンド

```bash
uv sync                       # 依存をインストール（.venv 構築）
uv add <package>              # 実行時依存を追加（例: fastapi uvicorn pydantic）
uv add --dev <package>        # 開発依存を追加（例: pytest httpx ruff）
uv run uvicorn app.main:app --reload   # 開発サーバ起動（ホットリロード）
uv run ruff format .          # フォーマット
uv run ruff check .           # lint
uv run pytest                 # テスト全体
uv run pytest <path>::<test>  # 単一テスト実行
```

***

## アーキテクチャ / 設計方針

### データロード

- 起動時（FastAPI の lifespan）に `assets/data/` を走査し、JSON を Pydantic モデルへ読み込んで**メモリ内ストア**（dict ベースのインデックス: `entry_no → 単語`、`idiom_id → 慣用句`、`section`・`pos_category` 別リスト等）を構築する。
- スキーマは「データスキーマ（参照仕様）」節を**唯一の正**として Pydantic モデル化する。全フィールド optional 前提・欠落は省略されている点に注意（モデルでも `Optional` / デフォルト値で受ける）。
- データは静的なので**読み取り専用**。書き込み系エンドポイントは設けない。

### 画像配信

- `assets/manga/` をそのまま静的公開（例: `GET /assets/manga/part1/001.png`）。
- 単語/慣用句レスポンスの `image_url`（または `image_path`）でクライアントに参照させる。バイナリを JSON に埋め込まない。

### API エンドポイント（実装済み）

読み取り専用の REST。プレフィックスは `/api`。全レスポンスは Pydantic モデルで型固定、`image_url` を含む（詳細系は `response_model_exclude_none=True` で欠落フィールドを省略）。

| メソッド・パス | 役割 | 主な query |
|---|---|---|
| `GET /healthz` | ヘルスチェック（ロード件数） | — |
| `GET /api/meta` | 区分・件数・`pos_category` 内訳 | — |
| `GET /api/words` | 単語一覧 | `section`(part1/part2/keigo) / `pos` / `q` / `ids`(カンマ区切り・順序保持) / `limit` / `offset` |
| `GET /api/words/{entry_no}` | 単語詳細（例 `001`） | — |
| `GET /api/idioms` | 慣用句一覧 | `q` / `ids` / `limit` / `offset` |
| `GET /api/idioms/{idiom_id}` | 慣用句詳細（例 `kobun-kanyouku-10_0`） | — |
| `GET /api/search` | 単語・慣用句の横断検索 | `q`(必須) / `limit` |
| `GET /api/quiz` | 4択クイズ素材（同 pos 優先のダミー選択肢＋`answer_index`） | `section` / `pos` / `count` / `choices` |
| `GET /assets/manga/...` | 暗記カード画像（`StaticFiles`） | — |

- `image_url` は `KOBUN_ASSET_BASE_URL`（既定 `""`→`/assets/...`）を前置。Caddy 配下では `/kobun` 等を設定。
- アプリの学習進捗・SRS・お気に入り・設定・学習状態・「入試重要」フラグは **API 範囲外**（端末保持）。新エンドポイント追加は**勝手に増やさず確認**する。

### デプロイ（docker-compose / Caddy 統合）— 設定追加済み

- ポートは **8006**（兄弟サービスと重複しない次の空き）。`Dockerfile` は `python:3.12-slim` + `uv`、`CMD uv run uvicorn app.main:app --port 8006`。
- 親リポジトリ `myserver/docker-compose.yml` に **`kobun-api` サービスを追加済み**（`build: ./kobun`, `8006:8006`, `env_file: .env`, `./kobun:/app`）。**DB 不要**なので `postgres`/`depends_on` は付けない。
- 親 `caddy/Caddyfile` に **`route /kobun* { uri strip_prefix /kobun; reverse_proxy kobun-api:8006 }` を追加済み**（画像も同プロキシ経由。必要なら Caddy `file_server` 直配信へ最適化可）。
- 公開 URL は **`https://forecargo.ngrok.app/kobun`**（iOS アプリ `../kobunApp` の既定接続先）。
- 環境変数: `KOBUN_DATA_DIR` / `KOBUN_ASSETS_DIR` / `KOBUN_ASSET_BASE_URL`（いずれも任意・既定値あり）。

> **注意（要再読込）**: 稼働中の `caddy` コンテナは設定追加より前に起動したままなので、`/kobun` ルートは**まだ反映されていない**。反映には `docker compose restart caddy` が必要（全サービスが一瞬切断される）。

### 起動方法

```bash
# A. 本番同様（Docker・ngrok 公開）
cd /Users/nobuhiro/Python/myserver
docker compose up -d --build kobun-api
docker compose restart caddy          # /kobun ルートを反映（全サービス一瞬切断）
curl -s https://forecargo.ngrok.app/kobun/healthz   # {"status":"ok","words":315,"idioms":65}

# B. ローカル開発（手軽）。アプリの接続先は http://localhost:8006 に切り替える
cd /Users/nobuhiro/Python/myserver/kobun
uv run uvicorn app.main:app --port 8006
curl -s http://localhost:8006/healthz
```

### 関連リポジトリ

- 本 API を利用する iOS クライアント: **`../kobunApp`**（SwiftUI、スケルトン実装済み・ビルド確認済み）。詳細は `../kobunApp/CLAUDE.md`。

***

## ディレクトリ構成（実装済み）

```
kobun/
├── app/                  # FastAPI アプリ本体
│   ├── main.py           #   app 生成・lifespan(store)・CORS・StaticFiles マウント・/healthz
│   ├── config.py         #   os.getenv 設定・section ラベル・image_url 生成
│   ├── deps.py           #   get_store 依存性
│   ├── models.py         #   Pydantic v2 レスポンスモデル
│   ├── store.py          #   assets/data ロード＆インメモリ索引・検索・クイズ
│   └── routers/          #   meta.py / words.py / idioms.py / search.py / quiz.py
├── tests/                # pytest（store / words / idioms / meta_search / quiz）
├── assets/               # 配信データ（JSON + 画像）※読み取り専用
│   ├── data/             #   part1 / part2 / keigo / kanyouku
│   └── manga/
├── pyproject.toml        # uv: fastapi, uvicorn[standard], pydantic / dev: pytest, httpx, ruff
├── .python-version       # 3.12
├── Dockerfile            # python:3.12-slim + uv（CMD: uvicorn app.main:app --port 8006）
├── .dockerignore
├── README.md
└── CLAUDE.md
```

***

## データスキーマ（参照仕様）

API レスポンスの**元仕様**。`assets/data/` の JSON はすべてこのスキーマに従う。全フィールド optional 前提・欠落は省略。Pydantic モデルはこれを正として定義する。

### 単語スキーマ（part1 / part2 / keigo 共通）

ファイル単位（画像1枚＝1JSON）:

```json
{
  "image_file": "Part1/kobun - 2.jpg",
  "printed_page": 37,
  "pos_category": "動詞",
  "entries": [ { /* 下記エントリ */ } ]
}
```

エントリ:

```json
{
  "entry_no": "003",
  "pages": [37],
  "headword": "見ゆ",
  "headword_variants": [],
  "reading": "みゆ",
  "sub_glosses": [],
  "conjugation_type": "ヤ行下二段",
  "meanings": [
    { "no": 1, "gloss": "見える・思われる" },
    { "no": 2, "gloss": "見られる・見せる" }
  ],
  "word_formation": "見ゆ＝見＋自発・受身・可能",
  "semantic_shift": null,
  "honorific": null,
  "related_words": [
    { "marker": "関", "word": "", "reading": "", "meanings": [] }
  ],
  "commentary": "「見ゆ」は「ゆ」に自発・可能・受身…",
  "examples": [
    {
      "sense_no": 1,
      "marker": null,
      "text": "都の中をも見え思われ所のさまなり。",
      "target_words": ["見え", "思われ"],
      "translation": "都の中とも見え思われる場所の様子である。",
      "source": "竹取・四段"
    }
  ],
  "illustration": { "present": false, "caption": "", "description": "" },
  "tip_box": "",
  "mistake_note": { "wrong": "", "correct": "", "note": "" },
  "qr_code": true,
  "manga": {
    "concept": "覚え方の設計メモ（日本語）",
    "prompt": "画像生成プロンプト（生成済みのため API では通常未使用）",
    "image_path": "assets/manga/part1/003.png",
    "status": "generated"
  }
}
```

フィールド補足:

- `entry_no` … 3桁ゼロ埋めの一意キー（通し番号 001〜315）。
- `pages` … 誌面ページ番号の配列（ページまたぎは複数）。
- `headword_variants` / `sub_glosses` … 異形・別表記。無ければ空配列。
- `conjugation_type` … 活用の種類。活用しない語（副詞等）では欠落/null。
- `meanings[]` … 丸囲み数字の語義。`no` と `gloss`。
- `semantic_shift` … 古/現の意味対比（主に名詞）。`{ "modern": "...", "classical": "..." }` か `null`。
- `honorific` … **敬語（keigo）のみ**。`{ "type": "尊敬|謙譲|丁寧", "base_word": "言ふ" }`。それ以外 `null`。
- `related_words[]` … `関`（関連）/`同`（同義）/`反`（反対）マーカー付きの関連語。
- `examples[]` … 語義番号 `sense_no` ごとの例文。`text`（古文原文）/`translation`（現代語訳）/`source`（出典、原文記法のまま）/`target_words`（強調語）。
- `mistake_note` … 誤用注意（×/○）。`manga` … 暗記カード（`image_path` = 配信画像、`status` = 全件 `generated`）。

### 慣用句スキーマ（kanyouku は別系統）

慣用句は**見出し番号なし**（識別子は見出し語、API ID は `{ファイル名}_{index}`）。同形異義は `senses`（`label` A/B）でまとめる。

```json
{
  "image_file": "kanyouku/kobun-kanyouku - 10.jpg",
  "printed_page": 267,
  "idioms": [
    {
      "headword": "さらぬ",
      "reading": "さらぬ",
      "senses": [
        { "label": "A", "writing": "然らぬ", "meanings": [{ "no": 1, "gloss": "そうではない・それ以外の" }] },
        { "label": "B", "writing": "避らぬ", "meanings": [{ "no": 1, "gloss": "避けられない" }] }
      ],
      "commentary": "「さ＋あら」がつづまった「さら」に…",
      "examples": [
        { "sense_label": "B", "marker": null, "text": "…さらぬ別れ…", "target_words": ["さらぬ別れ"], "translation": "…", "source": "源氏・松風" }
      ],
      "related": [],
      "manga": { "concept": "", "prompt": "", "image_path": "assets/manga/kanyouku/kobun-kanyouku-10_0.png", "status": "generated" }
    }
  ]
}
```

- 同形異義が無い慣用句は `senses` を持たず、直下に `meanings[]` を置く（`assets/data/kanyouku/` には両パターンが存在する）。
- 親語に複数の関連慣用句がぶら下がる紙面があり、関連は `related[]` に格納される。
- `examples[].sense_label` … `senses` 使用時に対応する `label`。未使用時は `null`。

***

## 開発の方針

- **データは読み取り専用**。API 実装でデータ内容を変えない。誤りを見つけた場合のみ `assets/data/` の該当 JSON を直接修正し、画像参照（`image_path`）との整合を保つ。
- **スキーマは上記「参照仕様」が正**。新しいフィールドを見つけたら勝手に無視・改変せず、モデルに反映するか確認する（全フィールド optional・欠落省略を前提に堅牢にパースする）。
- グローバル規約（型ヒント・Google スタイル docstring・ruff・pytest・guard clause・`logging` 使用・機密情報のハードコード禁止）を遵守する。
- スコープ厳守。指示されていない機能追加・リファクタは行わず、要件が曖昧なら実装前に確認する。
