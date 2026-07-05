# kobun-api — 古文単語アプリ「ことだま」コンテンツ配信 API

古文単語アプリ「ことだま」（iOS）へ、確定済みの**単語・慣用句データと暗記カード画像**を配信する読み取り専用 API サーバ。

## 目的

`assets/` 配下のデータ化成果物（単語 315 件・慣用句 65 件・カード画像 380 枚）を、アプリが利用しやすい JSON / 静的画像として提供する。学習進捗・SRS・設定などのユーザー状態は端末側に保持し、本 API は**コンテンツ配信のみ**を担う（認証・DB 不要）。

## 前提条件

- Python 3.12（`.python-version` で pin）
- [uv](https://docs.astral.sh/uv/)

## セットアップ

```bash
uv sync                                       # 依存をインストール
uv run uvicorn app.main:app --reload          # 開発サーバ（http://127.0.0.1:8000）
uv run pytest                                 # テスト
uv run ruff format . && uv run ruff check .   # フォーマット / lint
```

## 使い方（主なエンドポイント）

| メソッド・パス | 役割 |
|---|---|
| `GET /healthz` | ヘルスチェック（ロード件数） |
| `GET /api/meta` | 区分・件数・品詞内訳 |
| `GET /api/words` | 単語一覧（`section`/`pos`/`q`/`ids`/ページング） |
| `GET /api/words/{entry_no}` | 単語詳細 |
| `GET /api/idioms` | 慣用句一覧（`q`/`ids`/ページング） |
| `GET /api/idioms/{idiom_id}` | 慣用句詳細 |
| `GET /api/search` | 単語・慣用句の横断検索 |
| `GET /api/quiz` | 4択クイズ素材 |
| `GET /assets/manga/...` | 暗記カード画像（静的配信） |

## アーキテクチャ概要

起動時に `assets/data/**/*.json` を全件メモリ展開し、`entry_no` / `idiom_id` などのインデックスを構築。検索・クイズもメモリ上で完結する。画像は `StaticFiles` で `/assets` にマウントして配信する。詳細は `CLAUDE.md` を参照。
