# CLAUDE.md — Mermaid フローチャートエディタ

Claude Code への指示書。このファイルを読んだうえで実装を進めること。

---

## プロジェクト概要

自然言語（チャット）で AI に指示しながら、Mermaid 形式のフローチャートをリアルタイムに編集・プレビューできる**個人用 Web アプリ**。

- ユーザー：開発者本人のみ（シングルユーザー）
- 認証：Caddy の Basic 認証（ngrok 経由でインターネット公開されるため）
- デプロイ：上位ディレクトリの Docker Compose（`/Users/nobuhiro/Python/myserver/`）に統合

---

## myserver スタックへの統合設計

```
インターネット → ngrok(forecargo.ngrok.app) → Caddy(:80) → mermaid-api:8004
```

### ポート

**8004**（既存: ocr-api:8000, guideline-api:8001, trouble-api:8002, gpt-image:8003）

### Caddy ルーティング（`/Users/nobuhiro/Python/myserver/caddy/Caddyfile`）

```caddyfile
# アセットは認証不要（ブラウザが <script crossorigin> でサブリソースを取得する際に
# Basic認証ヘッダーを自動送信しないため、JS/CSSが読み込まれず画面が真っ白になる）
route /mermaid/assets* {
    uri strip_prefix /mermaid
    reverse_proxy mermaid-api:8004
}

# アプリ本体・APIは Basic 認証必須
route /mermaid* {
    basic_auth {
        ncbmermaid <REDACTED-ROTATED-HASH>
    }
    uri strip_prefix /mermaid
    reverse_proxy mermaid-api:8004 {
        flush_interval -1    # SSE のため即時フラッシュ必須
    }
}
```

**ユーザー名 / パスワード**: `ncbmermaid` / `mermaid2024`

ハッシュ再生成:
```bash
docker run --rm caddy:2-alpine caddy hash-password --plaintext 'PASSWORD'
```

Caddy が `/mermaid` を strip するため、**コンテナ内部は `/` ベース**。

### docker-compose.yml への追加（`/Users/nobuhiro/Python/myserver/docker-compose.yml`）

```yaml
mermaid-api:
  build:
    context: ./mermaid-api          # backend/ と frontend/ 両方を参照できる
    dockerfile: backend/Dockerfile
  restart: unless-stopped
  ports:
    - "8004:8004"
  env_file:
    - .env
  environment:
    MERMAID_DATABASE_URL: sqlite+aiosqlite:///./data/app.db
    CLAUDE_MODEL: claude-sonnet-4-6
  volumes:
    - ./mermaid-api/data:/app/data  # SQLite ファイルをホストに永続化
```

### .env（`/Users/nobuhiro/Python/myserver/.env`）

```env
ANTHROPIC_API_KEY=sk-ant-...   # 設定済み
```

---

## ディレクトリ構成

```
mermaid-api/
├── CLAUD.md
├── data/                       # SQLite DB（.gitignore 対象）
├── backend/
│   ├── Dockerfile              # マルチステージ: node:20-alpine(ビルド) + python:3.11-slim(実行)
│   ├── requirements.txt
│   ├── main.py                 # FastAPI エントリーポイント + 静的ファイル配信 + SPA fallback
│   ├── database.py             # SQLAlchemy async + SQLite (WAL mode)
│   ├── models.py               # Project / Diagram / Message
│   ├── schemas.py              # Pydantic v2
│   └── routers/
│       ├── __init__.py
│       ├── projects.py
│       ├── diagrams.py
│       └── chat.py             # Anthropic SDK SSE ストリーミング
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    ├── tailwind.config.js
    ├── postcss.config.js
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        ├── vite-env.d.ts
        ├── api/
        │   └── client.ts       # fetch + ReadableStream SSE クライアント
        ├── components/
        │   ├── Sidebar.tsx     # プロジェクト・ダイアグラム一覧・作成・削除
        │   ├── ChatPanel.tsx   # SSEストリーミングチャット UI
        │   ├── PreviewPanel.tsx # mermaid.js リアルタイムプレビュー
        │   ├── CodeEditor.tsx  # Monaco Editor（lazy import）
        │   └── ExportMenu.tsx  # PNG / SVG / Markdown エクスポート
        └── store/
            └── appStore.ts     # Zustand グローバルストア
```

---

## 技術スタック

### バックエンド

| 項目 | 選定 |
|------|------|
| 言語 | Python 3.11+ |
| フレームワーク | FastAPI 0.115 |
| DB | SQLite（`./data/app.db`、WAL モード） |
| ORM | SQLAlchemy 2.x（async + aiosqlite） |
| AI | Anthropic Python SDK（`anthropic>=0.40.0`） |
| ストリーミング | Server-Sent Events（SSE） |
| モデル | `claude-sonnet-4-6`（環境変数 `CLAUDE_MODEL` で上書き可） |

### フロントエンド

| 項目 | 選定 |
|------|------|
| フレームワーク | React 18 + TypeScript |
| ビルド | Vite 6 |
| 図レンダリング | mermaid.js 11 |
| コードエディタ | Monaco Editor（`@monaco-editor/react`、lazy import） |
| 状態管理 | Zustand 5 |
| スタイル | Tailwind CSS 3 |
| HTTP/SSE | fetch + ReadableStream（EventSource は POST 非対応のため不可） |

---

## Docker 戦略（マルチステージビルド・1 コンテナ）

```dockerfile
# Stage 1: React ビルド
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: FastAPI + 静的ファイル
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=frontend-builder /frontend/dist ./static
RUN mkdir -p /app/data
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
```

**build context は `./mermaid-api`**（docker-compose.yml から `context: ./mermaid-api`）。

起動コマンド:
```bash
cd /Users/nobuhiro/Python/myserver
docker compose up -d mermaid-api
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

---

## URL プレフィックス設計

| レイヤー | 設定 |
|---------|------|
| Vite `base` | `'/mermaid/'`（本番）/ `'/'`（開発: `process.env.NODE_ENV !== 'production'` で分岐） |
| React Router | `<BrowserRouter basename="/mermaid">` |
| FastAPI | 内部ルートは `/api/...`（Caddy が `/mermaid` を strip するため `/` ベース） |

**仕組み**:
1. ブラウザが `https://forecargo.ngrok.app/mermaid/` をリクエスト
2. Caddy の Basic 認証を通過後、`/mermaid` を strip して FastAPI の `/` へ
3. FastAPI の SPA fallback が `static/index.html` を返す
4. HTML 内の `<script src="/mermaid/assets/...">` をブラウザが取得
5. Caddy の `/mermaid/assets*` ルート（認証なし）が strip → FastAPI の `/assets/...` StaticFiles が応答

**注意**: `<script crossorigin>` タグのサブリソース取得では、ブラウザが Basic 認証ヘッダーを自動送信しない。このため `/mermaid/assets*` を認証なしルートに分離している（認証なしでもアセットはただの JS バンドルであり機密情報は含まない）。

---

## 画面レイアウト

```
┌─────────────────────────────────────────────────────────────────────┐
│ [ヘッダー] ダイアグラム名  [プレビュー|コード]  [.md][SVG][PNG]       │
├────────────┬──────────────────────────────┬────────────────────────┤
│ サイドバー  │  左ペイン (flex-1)           │  右ペイン: チャット     │
│ (w-56)     │                              │  (w-1/3, min-w-72)     │
│            │  ┌─[ズームバー]──[− 100% +]┐│                        │
│ Projects   │  │                          ││  チャット履歴          │
│  > Proj A  │  │ [プレビュー]             ││  ────────────────────  │
│    - 図1   │  │ mermaid.js レンダリング  ││  対象チップ            │
│    - 図2   │  │ クリックで要素選択        ││  textarea (100-240px)  │
│  + 新規    │  │                          ││  [送信]                │
│            │  │ または [Monaco エディタ] ││  ※ Cmd+Enter で送信    │
│            │  └──────────────────────────┘│                        │
└────────────┴──────────────────────────────┴────────────────────────┘
```

- ルートは `100dvh`（iOS/iPadOS Safari の URL バー考慮）
- サイドバーの追加ボタンは `+` クリックのみ（Enter キー送信は無効）
- サイドバーは折りたたみ可能（`◀` / `▶` ボタン）。展開 `w-56` ⇔ 折りたたみ `w-10`。状態は `localStorage` の `mermaid-sidebar-collapsed` キーに保存

---

## データモデル

```sql
CREATE TABLE projects (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE diagrams (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name       TEXT NOT NULL,
    mermaid_code TEXT NOT NULL DEFAULT 'sequenceDiagram\n    actor 担当者\n    participant システム\n    担当者->>システム: リクエスト\n    システム-->>担当者: レスポンス',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    diagram_id INTEGER NOT NULL REFERENCES diagrams(id) ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content    TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## API 設計

### プロジェクト
```
GET    /api/projects                  # 一覧
POST   /api/projects                  # 作成 {name}
DELETE /api/projects/{id}             # 削除
```

### 図
```
GET    /api/projects/{id}/diagrams    # 一覧
POST   /api/projects/{id}/diagrams    # 作成 {name}
GET    /api/diagrams/{id}             # 取得（コード・チャット履歴含む）
PATCH  /api/diagrams/{id}             # 更新 {name?, mermaid_code?}
DELETE /api/diagrams/{id}             # 削除
```

### チャット（AI）
```
POST   /api/diagrams/{id}/chat        # メッセージ送信
                                      # Body: {message: string}
                                      # Response: text/event-stream (SSE)
```

### SSE のイベント形式
```
event: token
data: {"type": "token", "content": "..."}    # トークン逐次配信

event: mermaid
data: {"type": "mermaid", "code": "flowchart TD\n..."}  # DB更新後に送信

event: done
data: {"type": "done"}

event: error
data: {"type": "error", "message": "..."}
```

**chat.py の SSE 設計**:
- Anthropic SDK の `client.messages.stream()` でトークンを逐次 yield
- 全応答完了後、正規表現で ` ```mermaid...``` ` を抽出 → `diagrams.mermaid_code` を DB 更新 → `mermaid` イベント送信
- チャット履歴: 直近 20 件のみ Anthropic に送信（トークン管理）
- SSE generator 内は `async_session_factory()` を独立して使う（`Depends(get_session)` スコープ問題を回避）
- フロントエンド側は `done` イベント受信後に `GET /api/diagrams/{id}` で詳細を再取得してチャット履歴を更新

---

## AI システムプロンプト

メインターゲットは **sequenceDiagram**（シーケンス図）。実装は `backend/routers/chat.py` の `_SYSTEM_PROMPT` 参照。

骨子:

```
あなたは Mermaid シーケンス図の編集アシスタントです。

## 必須ルール
1. 応答には必ず最新の完全な Mermaid コードを含めること
2. Mermaid コードは必ず ```mermaid ～ ``` で囲むこと
3. コードブロック以外に、変更内容の簡単な説明（日本語）を書くこと
4. コードは常に有効な Mermaid 構文であること

## sequenceDiagram の構文ルール
- 参加者宣言: `actor`（人）/ `participant`（システム）
- メッセージ: `->>` 同期 / `-->>` 戻り / `-)` 非同期 / `--x` 失敗
- 制御構造: loop / alt-else / opt / par-and
- 注釈: Note over / right of
- メッセージ名は「動詞＋目的語」の日本語

## 対応する図の種類
- sequenceDiagram（シーケンス図）← メイン
- flowchart（フローチャート）
- classDiagram（クラス図）
- stateDiagram-v2（状態遷移図）
- erDiagram（ER 図）

## 現在の Mermaid コード
{current_mermaid_code}
```

**Python `str.format()` 注意**: プロンプト内の `{...}` は `{{...}}` にエスケープすること（`{current_mermaid_code}` は除く）。

---

## プレビュー UI 機能（PreviewPanel.tsx）

### 要素選択（チャットの文脈付与）

SVG 上の要素をクリックして、チャット送信時に対象を LLM に明示できる。

| 種別 | クリック対象 | 検出セレクタ | LLM へのプレフィックス |
|------|-------------|-------------|----------------------|
| 参加者 | sequenceDiagram の参加者ボックス（actor/participant） | `text.actor` / `rect.actor` | `[対象参加者: 名前]` |
| 処理 | sequenceDiagram のメッセージ矢印ラベル | `text.messageText` | `[対象処理: 内容]` |
| 制御ブロック | sequenceDiagram の loop / alt / opt / par 等のキーワード・条件・枠線 | `text.labelText` / `text.loopText` / `rect.labelBox` / `rect.loopLine` | `[対象ブロック: loop: 条件]` |
| flowchart ノード | flowchart のノード | `.node`（ID は `flowchart-{id}-{n}`） | `[対象参加者: ラベル]` |

選択中はハイライト表示（indigo 系）。選択状態は `appStore.ts` の `SelectedNode { nodeId, nodeLabel, type: "participant" | "message" | "block" }` で管理。

### ズーム機能

| 操作 | 挙動 |
|------|------|
| ツールバーの `−` / `＋` | 25% 刻み（min 25%, max 400%） |
| ツールバーの `100%` | リセット |
| Ctrl/Cmd + ホイール | 連続ズーム |

**実装上のポイント**:
- ホイールイベントは `document` レベルで `passive: false` 登録 → Safari の passive 制限を回避
- ズームコントロールはスクロール領域の**外**に固定配置 → Safari の `position: sticky` + `pointer-events: none` バグ回避
- `applySvgWidth`:
  - viewBox から自然なアスペクト比を取得し、SVG の width/height を **px 値で明示**指定（`height: auto` は Safari で信頼性が低いため）
  - mermaid が SVG に埋め込む `style="max-width: <自然幅>"` を `style.maxWidth = "none"` で打ち消し（これがないと横方向の拡大が頭打ちになる）
  - scale > 1 の時はコンテナ div の width も明示的に拡張 → スクロール領域の scrollWidth が広がり横スクロール可能になる
  - `containerRef` は `scrollRef` の直接の子（中間 div の `width: 100%` が scrollWidth を制限するのを避けるため）

---

## エクスポート機能

### PNG / SVG
- DOM から `<svg>` 要素を取得（mermaid.js がレンダリング済み）
- PNG：`<canvas>` に描画して `toBlob()` でダウンロード
- SVG：`outerHTML` を Blob としてダウンロード

### Markdown
```markdown
# {図名}

```mermaid
{mermaid_code}
```
```

---

## 環境変数

```env
# 上位 .env（/Users/nobuhiro/Python/myserver/.env）
ANTHROPIC_API_KEY=sk-ant-...        # 設定済み

# docker-compose.yml の environment: で設定（既存 DATABASE_URL=PostgreSQL と衝突しないよう別名）
MERMAID_DATABASE_URL=sqlite+aiosqlite:///./data/app.db
CLAUDE_MODEL=claude-sonnet-4-6      # デフォルト値
```

---

## チャット UI（ChatPanel.tsx）

- 送信ショートカット: **Cmd+Enter**（Enter 単独では改行）
- textarea は自動リサイズ（`scrollHeight` 反映、`min-h-[100px] max-h-[240px]`）
- 選択中の要素はチップとして入力欄上に表示（× で解除）
- 送信時、選択チップが付いていればメッセージ先頭に `[対象参加者: ...]` / `[対象処理: ...]` / `[対象ブロック: ...]` を自動付与し、選択は解除される

---

## 注意事項・制約

- **アセット認証分離**: `/mermaid/assets*` を認証なしルートに配置。`<script crossorigin>` タグのサブリソース取得でブラウザが Basic 認証ヘッダーを自動送信しない問題を回避するため。
- **CORS**: 本番は同一オリジン（Caddy 経由）のため不要。開発時は Vite proxy（`/api` → `localhost:8004`）で対応。
- **API URL の base 解決**: `frontend/src/api/client.ts` で `BASE = ${import.meta.env.BASE_URL}api`。本番 `/mermaid/api`、開発 `/api`。
- **mermaid 動的インポート**: `PreviewPanel.tsx` では `import("mermaid")` の lazy singleton（モジュール先頭の `mermaid.initialize()` を呼ぶと Vite 環境下でクラッシュするため）。
- **ErrorBoundary**: `main.tsx` でアプリ全体をラップ（mermaid のレンダーエラーで真っ白画面を回避）。
- **SQLite WAL モード**: `database.py` で `PRAGMA journal_mode=WAL` を設定。
- **Monaco の bundle サイズ**: ~5MB のため `React.lazy()` で遅延ロード。
- **Mermaid コード検証**: AI が無効なコードを返した場合、`mermaid.render()` の Promise reject をキャッチしてエラー表示（プレビューは前の状態を維持）。
- **APIキー**: `.env` ファイルで管理し、Git にコミットしないこと。
- **コードエディタの自動保存**: Monaco で編集後 1 秒後に `PATCH /api/diagrams/{id}` で自動保存。
- **iOS/iPadOS Safari**: ルート要素は `100vh` ではなく `100dvh`（URL バー切替で入力欄が画面外に隠れる問題を回避）。
