# trouble-api

NCBオンライン（ncbonline@nttdata-ncb.co.jp）から届くシステム障害通知メールを自動収集・解析し、障害情報をPostgreSQLで一元管理するFastAPIサービス。

- ポート: `8002`
- Caddy経由: `https://<host>/trouble/*`
- Web UI: `https://<host>/trouble/`（`?id=<id>` でインシデント詳細を直接表示）

## ファイル構成

```
trouble-api/
├── main.py             # FastAPI app・エンドポイント・lifespan
├── models.py           # SQLAlchemy ORM + Pydantic スキーマ
├── collector.py        # IMAP メール収集・インシデント登録
├── analyzer.py         # Gemini LLM による構造化抽出
├── database.py         # SQLAlchemy engine・セッション管理
├── scheduler.py        # APScheduler バックグラウンドタスク
├── line_handler.py     # LINE Messaging API 連携（通知・Bot）
├── setup_richmenu.py   # LINE リッチメニュー初期設定スクリプト（ホストで実行）
├── static/
│   └── index.html      # 管理 Web UI（SPA）
├── requirements.txt
└── Dockerfile
```

## API エンドポイント

| Method | Path | 説明 |
|---|---|---|
| GET | / | 管理 Web UI |
| GET | /health | ヘルスチェック |
| GET | /incidents | インシデント一覧（クエリ: system_name, status, from_date, to_date, limit, offset） |
| GET | /incidents/{id} | インシデント詳細（JSON） |
| PUT | /incidents/{id} | 手動更新（ステータス修正等） |
| DELETE | /incidents/{id} | 削除 |
| POST | /sync | 即時メール同期（新規インシデントがあれば LINE 通知） |
| GET | /summary | システム別・ステータス別集計 |
| POST | /line/webhook | LINE Messaging API Webhook 受信 |

## データベーススキーマ

### incidents
| カラム | 型 | 説明 |
|---|---|---|
| id | Integer PK | |
| system_name | String(200) INDEX | 障害発生システム名 |
| failure_type | String(200) | 障害種別 |
| status | String(50) INDEX | 発生中 / 調査中 / 復旧済み |
| occurred_at | DateTime | 障害発生時刻（LLM抽出） |
| closed_at | DateTime | 復旧時刻 |
| description | Text | 障害詳細 |
| response | Text | 対応内容 |
| email_subject | String(500) | 元メール件名 |
| email_received_at | DateTime | メール受信時刻 |
| email_message_id | String(500) UNIQUE | 重複防止キー |
| raw_email_body | Text | 元メール本文 |
| created_at / updated_at | DateTime | |

**ステータス定義**
| ステータス | 意味 |
|---|---|
| 発生中 | 障害が発生し、まだ解決していない |
| 調査中 | 原因調査中または対応中 |
| 復旧済み | サービスが復旧・解決済み（根本原因調査中・完全クローズ問わず） |

### processed_emails
重複処理防止テーブル。収集済みの Message-ID を記録。

## 必要な環境変数（.env に追加）

```
# PostgreSQL
POSTGRES_DB=trouble
POSTGRES_USER=trouble
POSTGRES_PASSWORD=<パスワード>
DATABASE_URL=postgresql://trouble:<パスワード>@postgres:5432/trouble

# IMAP（docomo.ne.jp）
IMAP_HOST=imap.spmode.ne.jp
IMAP_PORT=993
IMAP_USERNAME=akahoshi@docomo.ne.jp
IMAP_PASSWORD=<IMAPパスワード>
SENDER_FILTER=ncbonline@nttdata-ncb.co.jp
SYNC_INTERVAL_MINUTES=15

# LINE Messaging API
LINE_CHANNEL_SECRET=<LINE Developers > チャンネル基本設定 > Channel secret>
LINE_CHANNEL_ACCESS_TOKEN=<Messaging API 設定 > Channel access token (long-lived)>
LINE_NOTIFICATION_TARGETS=<User ID または Group ID（カンマ区切り複数可）>
BASE_URL=https://forecargo.ngrok.app/trouble
```

> **注意**: docomoのIMAPパスワードはspモードパスワードではなく「メール設定 > IMAP/POP設定」で発行するアプリパスワード。

## LINE Messaging API 設定

### チャンネル設定
1. LINE Developers Console でチャンネル作成（Messaging API）
2. **Channel secret**: チャンネル基本設定 → Channel secret → `LINE_CHANNEL_SECRET` に設定
3. **Channel access token**: Messaging API 設定 → Channel access token (long-lived) → 発行して `LINE_CHANNEL_ACCESS_TOKEN` に設定

### Webhook URL 設定
LINE Developers Console → Messaging API 設定 → Webhook URL に登録：
```
https://forecargo.ngrok.app/trouble/line/webhook
```
「Webhookの利用」をオン → 「検証」ボタンで確認。

### 通知ターゲット ID の取得方法
- **自分の User ID**: LINE Developers Console → プロバイダー → チャンネル → Messaging API 設定 → 「あなたのユーザーID」
- **グループ ID**: Bot をグループに招待後、Webhook で受信する `source.groupId` を確認

```
LINE_NOTIFICATION_TARGETS=Uxxxxxxxxxxxx          # 個人のみ
LINE_NOTIFICATION_TARGETS=Uxxxxxxxxxxxx,Cxxxxxx  # 個人 + グループ
```

### リッチメニュー（チャット下部ボタン）のセットアップ
ホストマシンで一度だけ実行する。変更時も再実行すれば上書きされる。

```bash
pip install httpx Pillow
python trouble-api/setup_richmenu.py
```

4ボタン（2×2）が設定される：

| ボタン | 送信テキスト |
|---|---|
| 発生中（赤） | `発生中` |
| 一覧（青） | `一覧` |
| 同期（黄） | `同期` |
| ヘルプ（緑） | `ヘルプ` |

### Bot コマンド一覧
| コマンド | 説明 |
|---|---|
| 一覧 / リスト | 最新インシデント10件（Flex カルーセル） |
| 発生中 / 障害 | 未解決インシデント（発生中・調査中） |
| #123 | インシデント #123 の詳細 |
| 同期 / sync | メール同期を即時実行、件数を返信 |
| ヘルプ / help | コマンド一覧 |

Flex Message の「詳細 #123 →」ボタンは `BASE_URL/?id=123` を開き、Web UI でそのインシデントの詳細モーダルが自動表示される。

## 開発・デバッグポイント

### IMAP 接続確認
docomoのIMAPサーバーは `imap.spmode.ne.jp:993 (SSL)` を使用。
接続できない場合は下記を確認：
1. spモード メールアプリで「IMAP/SMTPによるメール受信」を有効化
2. docomo IDでMy docomoへログインし「メール設定」→「IMAP/POP設定」でアプリパスワード発行
3. `POST /sync` で手動トリガーして `errors` フィールドを確認

```bash
# Docker外から直接確認
python3 -c "
import imapclient
with imapclient.IMAPClient('imap.spmode.ne.jp', port=993, ssl=True) as s:
    s.login('akahoshi@docomo.ne.jp', '<パスワード>')
    print(s.list_folders())
"
```

### Gemini プロンプトのチューニング
`analyzer.py` の `ANALYSIS_PROMPT` を修正する。実際のメール文面で `POST /sync` 後に
`GET /incidents` のレスポンスを確認し、抽出精度を検証すること。

- `system_name` の揺れ（"NCBオンライン" vs "NCBシステム" 等）は `PUT /incidents/{id}` で正規化可能
- `is_update: true` の判定精度が低い場合、プロンプトに具体的な「続報」「復旧」等のキーワード例を追加

### 新規インシデント vs 更新の判定ロジック
`collector.py` の `_find_existing_incident()` が担当。

1. 同じ `system_name` でステータスが「発生中/調査中/復旧済み」のインシデントを検索
2. `occurred_at` が ±4時間以内なら同一インシデントとして更新
3. 該当なければ最新の未復旧インシデントにフォールバック
4. それでも見つからなければ新規作成

→ 誤マッチが多い場合は `timedelta(hours=4)` を調整するか、`system_name` の正規化を先に行う。

### DBマイグレーション
Alembicは使用せず、起動時に `Base.metadata.create_all()` でテーブルを自動作成。
カラム追加等のスキーマ変更は psql で直接 `ALTER TABLE` するか、PostgreSQL コンテナを
一度削除して再起動（`docker compose down -v && docker compose up`）。

### ログ確認
```bash
docker compose logs -f trouble-api
```

### 手動同期
```bash
curl -X POST http://localhost:8002/sync | jq
# または Caddy経由
curl -X POST http://localhost/trouble/sync | jq
```

### LINE Webhook 疎通テスト
```bash
# LINE_CHANNEL_SECRET 未設定時は署名検証をスキップ
curl -X POST http://localhost:8002/line/webhook \
  -H "Content-Type: application/json" \
  -d '{"events":[]}'
# → {"status":"ok"}
```
