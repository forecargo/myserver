# myserver

FastAPI バックエンドと iOS クライアントアプリを束ねたモノレポ。  
Docker Compose で全サービスをまとめて起動し、Caddy がリバースプロキシ・HTTPS 終端を担う。

## 構成

```
myserver/
├── ocr-api/          # スケジュール画像 → JSON 変換 API (port 8000)
├── guidline-api/     # 金融庁ガイドライン セマンティック検索 API (port 8001)
├── trouble-api/      # NCBオンライン障害通知メール管理 API (port 8002)
├── ScheduleScanner/  # iOS OCR クライアントアプリ (Xcode)
├── GuidlineSearch/   # iOS ガイドライン検索アプリ (Xcode/SwiftUI)
├── caddy/            # Caddyfile（リバースプロキシ設定）
└── docker-compose.yml
```

## サービス一覧

| サービス | 説明 | ポート |
|---|---|---|
| ocr-api | Gemini API による画像OCR・スケジュール構造化 | 8000 |
| guideline-api | BM25+セマンティックハイブリッド検索 | 8001 |
| trouble-api | 障害メール収集・LINE通知・LIFF UI | 8002 |
| caddy | HTTPS終端・リバースプロキシ・Basic認証 | 80 / 443 |
| postgres | 障害インシデント永続化 | 5432 |
| ngrok | 外部公開トンネル (`forecargo.ngrok.app`) | 4040 |

## クイックスタート

```bash
# 起動
make up

# ログ確認
make logs

# 停止
make down

# DBダンプ
make db-dump
```

## 環境変数

プロジェクトルートに `.env` を作成する。

```env
# Gemini
GEMINI_API_KEY=

# PostgreSQL
POSTGRES_DB=trouble
POSTGRES_USER=trouble
POSTGRES_PASSWORD=

DATABASE_URL=postgresql://trouble:<パスワード>@postgres:5432/trouble

# IMAP（docomo）
IMAP_HOST=imap.spmode.ne.jp
IMAP_PORT=993
IMAP_USERNAME=
IMAP_PASSWORD=
SENDER_FILTER=ncbonline@nttdata-ncb.co.jp
SYNC_INTERVAL_MINUTES=15

# LINE Messaging API
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
LINE_NOTIFICATION_TARGETS=
BASE_URL=https://forecargo.ngrok.app/trouble

# LIFF
LIFF_ID=

# ngrok
NGROK_AUTHTOKEN=
```

## 各サービスの詳細

- **ocr-api** → [ocr-api.md](./ocr-api.md)
- **guideline-api** → [guidline-api/guideline-api.md](./guidline-api/guideline-api.md)
- **trouble-api** → [trouble-api.md](./trouble-api.md)
- **ScheduleScanner (iOS)** → [Scanner.md](./Scanner.md)
- **GuidlineSearch (iOS)** → [GuidlineSearch/GuidlineSearch.md](./GuidlineSearch/GuidlineSearch.md)
- **ガイドライン検索 実装計画** → [guideline-search-plan.md](./guideline-search-plan.md)

## Caddy ルーティング

| パス | 転送先 | 認証 |
|---|---|---|
| `/schedule*` | ocr-api:8000 | なし |
| `/guideline*` | guideline-api:8001 | なし |
| `/trouble/line/webhook` | trouble-api:8002 | なし |
| `/trouble/liff*` | trouble-api:8002 | LIFF トークン |
| `/trouble*` | trouble-api:8002 | Basic 認証 |
