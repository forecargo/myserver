# gpt-image サービス

## 概要

OpenAI **gpt-image-2** を使用した画像生成 API + Web UI。テキストプロンプト・参照画像・マスク編集・マルチターン対話による高度な画像生成に対応する。

## 技術スタック

- Python 3.11 / FastAPI 0.115.0 / uvicorn 0.30.0
- openai >= 1.30.0
- Pillow >= 10.0.0（RGBA→RGB 自動変換）
- python-multipart >= 0.0.9（multipart/form-data 対応）
- Docker (python:3.11-slim)
- ポート: 8003

## ディレクトリ構造

```
gpt-image/
├── main.py              # FastAPI アプリ本体
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── run.sh               # ローカル起動スクリプト
├── CLAUDE.md
└── static/
    └── index.html       # Web UI（A案 左サイドバー + 2×2グリッド）
```

## 環境変数

| 変数名 | 説明 | 必須 |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API キー | ✅ |

起動時に未設定であれば `RuntimeError` で即停止する。

## エンドポイント一覧

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/` | Web UI (`/static/index.html`) へリダイレクト |
| GET | `/health` | ヘルスチェック → `{"status":"ok","model":"gpt-image-2"}` |
| POST | `/generate` | テキストのみ画像生成 (images.generate) |
| POST | `/edit` | 参照画像付き生成 (images.edit, multipart) |
| POST | `/edit/mask` | マスクによる部分編集 (images.edit + mask) |
| GET | `/generate/stream` | SSE ストリーミング生成 |
| POST | `/session/create` | Responses API マルチターン初回 |
| POST | `/session/continue` | previous_response_id で会話継続 |

---

### POST /generate

**リクエスト (JSON):**

```json
{
  "prompt": "a futuristic city at sunset",
  "size": "1024x1024",
  "quality": "auto",
  "n": 1,
  "output_format": "png"
}
```

| フィールド | 型 | デフォルト | 選択肢 |
|---|---|---|---|
| `prompt` | string | 必須 | 任意のテキスト |
| `size` | string | `1024x1024` | `auto` または 16px倍数のWxH形式 |
| `quality` | string | `auto` | `low` / `medium` / `high` / `auto` |
| `n` | int | `1` | 1〜10 |
| `output_format` | string | `png` | `png` / `jpeg` / `webp` |

**レスポンス (JSON):**

```json
{"images": ["<base64文字列>", ...], "format": "png"}
```

URL ではなく **base64** で返却する（OpenAI の一時 URL は有効期限が短いため）。

---

### POST /edit

参照画像を渡してキャラクター一貫性のある画像を生成する。

**リクエスト (multipart/form-data):**

| フィールド | 型 | 説明 |
|---|---|---|
| `prompt` | Form string | 必須 |
| `images` | 複数 UploadFile | 1〜10枚、各 50MB 未満 |
| `size`, `quality`, `n`, `output_format` | Form string/int | /generate と同様 |

- RGBA PNG は **バックエンドで自動的に白背景 RGB に変換**される。
- 変換されたファイル名は `rgba_converted` フィールドで返却。

---

### POST /edit/mask

生成済み画像の一部を書き換える。

**リクエスト (multipart/form-data):**

| フィールド | 型 | 説明 |
|---|---|---|
| `prompt` | Form string | 必須 |
| `image` | UploadFile | 編集対象の元画像 |
| `mask` | UploadFile | RGBA PNG（透明 alpha=0 が編集領域） |
| `size`, `quality`, `n` | Form | /generate と同様 |

マスクのルール:
- 透明 (alpha=0) → 書き換える領域
- 不透明 (alpha=255) → 保持する領域
- アルファチャンネル必須（RGBA PNG のみ）

---

### GET /generate/stream

SSE (Server-Sent Events) でストリーミング生成する。

**クエリパラメータ:** `prompt`, `size`, `quality`, `n`, `partial_images`（デフォルト 2）

**SSE イベント形式:**

```
data: {"type":"partial","index":1,"b64":"...","image_index":0}
data: {"type":"done"}
data: {"type":"error","message":"..."}
```

---

### POST /session/create

Responses API を使ったマルチターン生成の初回リクエスト。

**リクエスト (JSON):**

```json
{"prompt": "...", "size": "1024x1024", "quality": "auto", "output_format": "png"}
```

**レスポンス:** `{"session_id": "...", "response_id": "...", "images": [...]}`

---

### POST /session/continue

前回の生成結果を文脈として保持したまま追加指示を出す。

**リクエスト (JSON):**

```json
{"session_id": "...", "prompt": "背景をもっと明るくして"}
```

**レスポンス:** `{"session_id": "...", "response_id": "...", "images": [...], "turn": 2}`

---

## サイズ仕様（gpt-image-2）

- 両辺とも **16px の倍数**
- 各辺 **16〜3840px**
- 長辺と短辺の比率 **3:1 以内**
- 総ピクセル数 **655,360〜8,294,400**
- `"auto"` でモデルが最適サイズを選択

よく使うサイズ: `1024x1024`（SNSアイコン）, `1536x1024`（横長バナー）, `1024x1536`（ポートレート）, `2048x2048`（高解像度）

## コスト目安（gpt-image-2）

| quality | 1024x1024 |
|---|---|
| low | $0.006 |
| medium | $0.053 |
| high | $0.211 |

イテレーションは `low` で行い、最終出力だけ `high` にするのが実用的。

## ローカル起動

```bash
cd gpt-image
bash run.sh
# → http://localhost:8003
```

## Docker ビルド・起動

```bash
docker build -t gpt-image ./gpt-image
docker run -e OPENAI_API_KEY=sk-... -p 8003:8003 gpt-image
```

## 開発メモ

- **RGBA 変換**: 参照画像が透過 PNG (RGBA) の場合、API がエラーになる。バックエンドで Pillow を使って白背景 RGB に自動変換している。
- **セッション管理**: マルチターン用の `sessions` dict はメモリのみ。サーバー再起動でリセットされる。複数ワーカーが必要になった場合は Redis に移行する。
- **SSE と Caddy**: Caddy 経由でストリーミングを使う場合は Caddyfile に `flush_interval -1` が必要。
- **コスト削減**: 同一プロンプトへのキャッシュ（Redis 等）の検討を推奨。
- **gpt-image-2 制限**: 透過背景 (`background: "transparent"`) は現時点で非対応。複雑なプロンプトは最大 2 分かかることがある。
