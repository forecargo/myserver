# 金融庁ガイドラインセマンティック検索システム 実装計画

## Context

金融庁のサイバーセキュリティガイドライン（Markdown版）をセマンティック検索できるシステムを構築する。既存の `ocr-api` と同じパターン（FastAPI + Gemini API + Docker）で新しい `guideline-api` サービスを追加し、SwiftUI アプリ（GuidelineSearch）から検索できるようにする。

---

## 1. ディレクトリ構成

> **注意**: 既存ディレクトリ名は `guidline-api`（e なし）と `GuidlineSearch`（e なし）。以下もこの表記を使用する。

### guidline-api/ に追加するファイル

```
guidline-api/
├── 金融分野における...md   ← 既存（ソース文書）
├── main.py                 ← FastAPI アプリ本体
├── parser.py               ← Markdown チャンク分割ロジック
├── embedder.py             ← Gemini 埋め込み生成 + キャッシュ管理
├── searcher.py             ← コサイン類似度検索
├── models.py               ← Pydantic スキーマ定義
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

### GuidlineSearch/ に追加するファイル（Xcode プロジェクト）

```
GuidlineSearch/
├── DESIGN.md               ← 既存
├── project.yml             ← XcodeGen 定義
├── GuidlineSearch.xcodeproj/   ← xcodegen generate で生成
└── Sources/
    ├── App.swift
    ├── Assets.xcassets/
    ├── Models/
    │   └── GuidelineModels.swift
    ├── Services/
    │   └── SearchAPIService.swift
    ├── ViewModels/
    │   └── SearchViewModel.swift
    └── Views/
        ├── ContentView.swift
        ├── SearchBarView.swift
        ├── ResultCardView.swift
        ├── RequirementBadgeView.swift
        ├── ScoreBadgeView.swift
        ├── DetailView.swift
        └── DesignTokens.swift
```

---

## 2. API 設計

### エンドポイント

| Method | Path | 説明 |
|--------|------|------|
| GET | `/health` | ヘルスチェック |
| POST | `/search` | セマンティック検索 |

### リクエスト / レスポンス（models.py）

```python
class SearchRequest(BaseModel):
    query: str      # 検索キーワード
    top_k: int = 5  # 結果件数（1〜20）

class SearchResult(BaseModel):
    section_id: str          # "2.1.1"
    title: str               # 条項タイトル
    text: str                # チャンク全文
    snippet: str             # 先頭 200 文字（カード表示用）
    similarity_score: float  # 類似度 0〜100（%）
    requirement_type: str    # "basic" | "desirable" | "general"
    breadcrumb: str          # "2. ... > 2.1. ... > 2.1.1. ..."
    footnotes: list[dict]    # [{"ref": "^8", "text": "..."}]

class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str
    total_chunks: int
```

---

## 3. チャンク分割戦略（parser.py）

### アルゴリズム

1. **目次スキップ**: `## 目次` から次の `## ` ヘッダまでをスキップ
2. **ヘッダ追跡**: 行頭 `#` の深さでヘッダスタックを管理し、`breadcrumb` を構築
3. **要件タイプ分割**: 各サブセクション内で `【基本的な対応事項】` / `【対応が望ましい事項】` マーカーで分割
   - マーカー前の導入文 → `requirement_type = "general"`
   - マーカー後 → `"basic"` or `"desirable"`
4. **脚注処理**: `[^N]:` 行をサイドテーブルに収集し、チャンクのインライン参照に展開
5. **セクション番号**: `^(\d+\.\d+(?:\.\d+)*)` で heading から抽出

**想定チャンク数**: 約 95〜110 チャンク（インメモリ検索で十分）

---

## 4. 埋め込みとキャッシュ（embedder.py）

```python
# 起動時フロー
hash = sha256(guideline_md_file)
if cache_exists and cache["source_hash"] == hash:
    load embeddings from cache
else:
    for chunk in chunks:
        embedding = client.models.embed_content(
            model="text-embedding-004",
            content=chunk.text,
            config={"task_type": "RETRIEVAL_DOCUMENT"}
        )
        sleep(0.5)  # レート制限対策
    save to embeddings_cache.json with source_hash

# 検索時
query_embedding = client.models.embed_content(
    task_type="RETRIEVAL_QUERY"
)
```

**キャッシュ構造** (`embeddings_cache.json`):
```json
{
  "source_hash": "<sha256>",
  "chunks": [{"section_id": "...", "title": "...", "text": "...",
               "requirement_type": "...", "breadcrumb": "...",
               "footnotes": [], "embedding": [0.021, ...]}]
}
```

---

## 5. コサイン類似度検索（searcher.py）

```python
# NumPy のみ使用（外部 DB 不要）
embeddings_matrix = np.array([c.embedding for c in chunks])  # shape (N, 768)
norms = np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
normalized = embeddings_matrix / norms

def search(query_vec, top_k):
    q = query_vec / np.linalg.norm(query_vec)
    scores = normalized @ q
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [(chunks[i], scores[i] * 100) for i in top_indices]
```

---

## 6. インフラ変更

### docker-compose.yml に追加

```yaml
  guideline-api:
    build: ./guidline-api
    restart: unless-stopped
    ports:
      - "8001:8001"
    env_file:
      - .env
    volumes:
      - ./guidline-api:/app
```

### caddy/Caddyfile に追加

```
handle_path /guideline* {
    reverse_proxy guideline-api:8001
}
```

> `handle_path` でプレフィックス `/guideline` をストリップし、FastAPI 側は `/search` のまま受け取る。

---

## 7. SwiftUI アプリ（GuidlineSearch）

### 参照パターン
- `ScheduleScanner/Sources/Services/APIService.swift` — `actor` ベースの API クライアント
- `ScheduleScanner/Sources/Models/ScheduleModels.swift` — `Decodable` モデル定義
- `ScheduleScanner/Sources/ViewModels/ScheduleViewModel.swift` — `@MainActor ObservableObject`

### DesignTokens.swift（DESIGN.md より）

- `Color.deepNavy` → `#002045` (primary)
- `Color.surface` → `#faf9fd`
- `Color.basicBadgeBg` → `#d6e3ff` (primary-fixed)
- `Color.basicBadgeText` → `#001b3c` (on-primary-fixed)

### 主要コンポーネント

- **SearchBarView** — Navy テーマの検索フィールド
- **ResultCardView** — タイトル + スコアバッジ + breadcrumb + 要件タイプバッジ + スニペット
- **RequirementBadgeView** — 「基本対応」（青）/ 「望ましい対応」（緑）pill バッジ
- **DetailView** — 全文表示 + 脚注 DisclosureGroup

---

## 8. 実装順序

1. `parser.py` — チャンク分割
2. `embedder.py` — 埋め込み生成・キャッシュ
3. `searcher.py` — コサイン類似度検索
4. `main.py` + `Dockerfile` + `requirements.txt`
5. `docker-compose.yml` + `Caddyfile` 更新
6. SwiftUI: `GuidelineModels.swift` → `SearchAPIService.swift` → Views
7. `project.yml` → `xcodegen generate` → Xcode ビルド

---

## 9. 検証方法

```bash
# API ヘルスチェック
curl http://localhost:8001/health

# セマンティック検索テスト
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "パスワード認証 多要素認証", "top_k": 3}'
# → 期待: section 2.3.1 周辺が上位にランク

# Caddy 経由
curl -X POST http://localhost/guideline/search \
  -H "Content-Type: application/json" \
  -d '{"query": "サードパーティリスク", "top_k": 5}'
```

---

## 注意事項

- `embeddings_cache.json` は `.dockerignore` と `.gitignore` に追加する
- 初回起動時（キャッシュなし）は埋め込み生成に約 20 秒かかる
- ngrok は現状 `ocr-api:8000` のみにトンネルしているため、Swift アプリの開発中は `localhost:8001` を使う
