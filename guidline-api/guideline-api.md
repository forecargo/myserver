# Guideline Search API 仕様書

金融庁「金融分野におけるサイバーセキュリティに関するガイドライン」をセマンティック検索する FastAPI サービス。

## 概要

| 項目 | 内容 |
|------|------|
| ベースURL（直接） | `http://localhost:8001` |
| ベースURL（Caddy経由） | `http://localhost/guideline` |
| 認証 | なし |
| コンテンツタイプ | `application/json` |

## エンドポイント

### GET /health

サービスの稼働状態を確認する。

**レスポンス例**

```json
{
  "status": "ok",
  "chunks": 66
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `status` | string | `"ok"` |
| `chunks` | integer | インデックス済みチャンク総数 |

---

### POST /search

クエリテキストに対してセマンティック検索を実行し、関連するガイドライン条項を返す。

**リクエストボディ**

```json
{
  "query": "パスワード 多要素認証",
  "top_k": 5
}
```

| フィールド | 型 | 必須 | 説明 | 制約 |
|-----------|-----|------|------|------|
| `query` | string | ✓ | 検索クエリ | 1〜500文字 |
| `top_k` | integer | — | 返却件数（デフォルト: 5） | 1〜20 |

**レスポンスボディ**

```json
{
  "results": [
    {
      "section_id": "2.3.1",
      "title": "2.3.1. 認証・アクセス管理",
      "text": "- ① 認証及びアクセス権の付与に係る方針及び規程等を策定し...",
      "snippet": "- ① 認証及びアクセス権の付与に係る方針及び規程等を策定し...",
      "similarity_score": 71.5,
      "requirement_type": "basic",
      "breadcrumb": "2. サイバーセキュリティ管理態勢 > 2.3. サイバー攻撃の防御 > 2.3.1. 認証・アクセス管理",
      "footnotes": [
        {
          "ref": "^8",
          "text": "..."
        }
      ]
    }
  ],
  "query": "パスワード 多要素認証",
  "total_chunks": 66
}
```

**SearchResult フィールド**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `section_id` | string | セクション番号（例: `"2.3.1"`） |
| `title` | string | 条項タイトル（番号含む） |
| `text` | string | チャンク本文（全文） |
| `snippet` | string | 先頭200文字のプレビュー（カード表示用） |
| `similarity_score` | float | コサイン類似度スコア（0〜100、%表記） |
| `requirement_type` | string | `"basic"` \| `"desirable"` \| `"general"` |
| `breadcrumb` | string | `" > "` 区切りの階層パス |
| `footnotes` | array | インライン脚注の展開リスト |

**Footnote フィールド**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `ref` | string | 脚注参照ID（例: `"^8"`） |
| `text` | string | 脚注本文 |

**requirement_type の意味**

| 値 | 意味 |
|----|------|
| `"basic"` | 基本的な対応事項（金融機関等が一般的に実施すべき基礎的事項） |
| `"desirable"` | 対応が望ましい事項（大手金融機関等が参照すべき優良事例） |
| `"general"` | 一般的な説明文（要件区分なし） |

**エラーレスポンス**

| ステータス | 発生条件 |
|-----------|---------|
| 422 | リクエストバリデーションエラー（`query` が空など） |
| 502 | Gemini Embedding API 呼び出し失敗 |
| 503 | 起動中（埋め込みインデックス未構築） |

---

## 内部アーキテクチャ

```
ガイドラインMD
    ↓ parser.py
66チャンク（basic:36 / desirable:19 / general:11）
    ↓ embedder.py（起動時、キャッシュあれば即時）
埋め込みベクトル行列 (66 × 3072) ← gemini-embedding-001
    ↓ searcher.py（クエリ時）
コサイン類似度 → top-k チャンク返却
```

### 埋め込みキャッシュ

初回起動時、`embeddings_cache.json` を生成（約20秒）。以降はMDファイルのSHA-256が一致する限りキャッシュを使用する。MDファイルを更新した場合はキャッシュが自動再生成される。

---

## 利用例

```bash
# ヘルスチェック
curl http://localhost:8001/health

# セマンティック検索（直接）
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "ランサムウェア インシデント対応", "top_k": 3}'

# Caddy 経由
curl -X POST http://localhost/guideline/search \
  -H "Content-Type: application/json" \
  -d '{"query": "サードパーティリスク 外部委託", "top_k": 5}'
```
