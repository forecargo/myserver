# myserver 公開URL一覧

外部公開ドメイン: `forecargo.ngrok.app`（ngrok 経由で Caddy へトンネル）

## 公開URL一覧（FQDN付き）

| # | 公開URL | バックエンド | 認証 | 用途 |
|---|---|---|---|---|
| 1 | `https://forecargo.ngrok.app/ocr` | `ocr-api` | なし | OCR API |
| 2 | `https://forecargo.ngrok.app/schedule` | `ocr-api` | なし | スケジュール関連エンドポイント |
| 3 | `https://forecargo.ngrok.app/health` | `ocr-api` | なし | ヘルスチェック |
| 4 | `https://forecargo.ngrok.app/fudebako` | Caddy 静的配信 | なし | 静的サイト（`./fudebako`） |
| 5 | `https://forecargo.ngrok.app/guideline` | `guideline-api` | なし | 金融庁ガイドライン セマンティック検索 API |
| 6 | `https://forecargo.ngrok.app/trouble/line/webhook` | `trouble-api` | なし（LINE Webhook） | LINE Bot Webhook |
| 7 | `https://forecargo.ngrok.app/trouble/liff` | `trouble-api` | なし（LIFF） | LINE LIFF アプリ |
| 8 | `https://forecargo.ngrok.app/trouble` | `trouble-api` | **Basic** (`ncbtrouble`) | NCB障害通知メール管理 |
| 9 | `https://forecargo.ngrok.app/mermaid/assets` | `mermaid-api` | なし | Mermaid 静的アセット |
| 10 | `https://forecargo.ngrok.app/mermaid` | `mermaid-api` | **Basic** (`ncbmermaid`) | AI支援 Mermaid エディタ |
| 11 | `https://forecargo.ngrok.app/gpt-image` | `gpt-image` | **Basic** (`ncbgpt`) | GPT 画像生成 |

## 補足インフラ

| サービス | 役割 | 公開状態 |
|---|---|---|
| `caddy` | HTTPS 終端・リバースプロキシ・Basic 認証 | 80 / 443（ホスト） |
| `ngrok` | 外部トンネル（`forecargo.ngrok.app`） | 管理UI `http://localhost:4040`（ローカルのみ） |
| `postgres` | `trouble-api` 用 DB | 内部のみ（公開なし） |

## 認証情報の所在

Basic 認証のハッシュは `caddy/Caddyfile` に定義。ユーザー名のみ以下に記載（パスワードは別途管理）。

- `/trouble*` → `ncbtrouble`
- `/mermaid*` → `ncbmermaid`
- `/gpt-image*` → `ncbgpt`
