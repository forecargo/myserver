# trouble-api

NCBオンライン（ncbonline@nttdata-ncb.co.jp）から届くシステム障害通知メールを自動収集・解析し、障害情報をPostgreSQLで一元管理するFastAPIサービス。

- ポート: `8002`
- Caddy経由: `https://<host>/trouble/*`（Basic 認証あり）
- 管理 Web UI（Basic 認証）: `https://<host>/trouble/`
- LIFF UI（LINE認証）: `https://<host>/trouble/liff` → `https://liff.line.me/<LIFF_ID>`

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
│   └── index.html      # 管理 Web UI / LIFF UI（共用 SPA）
├── requirements.txt
└── Dockerfile
```

## セキュリティ

### Caddy ルーティングと認証

| 対象パス | 認証 |
|---|---|
| `/trouble/line/webhook` | **不要**（LINE プラットフォームからの Webhook） |
| `/trouble/liff*` | **不要**（LIFF トークン検証はアプリ内で実施） |
| `/trouble/*`（上記以外） | **必要**（Caddy Basic 認証） |

**ルート順序が重要**: `Caddyfile` では `/trouble/line/webhook` → `/trouble/liff*` → `/trouble*`（Basic 認証）の順に記述すること。

### LIFF 認証（ホワイトリスト制御）

`/liff/*` エンドポイントはリクエストの `Authorization: Bearer <LIFF_TOKEN>` を LINE API `/v2/profile` で検証し、`liff_allowed_users` テーブルに登録済みのユーザーのみアクセスを許可する（`_verify_liff_token()` in `main.py`）。

- 未登録ユーザー: HTTP 403 + LINE ID を含むエラーメッセージを返す
- 403 時に `liff_access_logs` テーブルへ自動記録（直近10件、同一ユーザーは `accessed_at` を更新）
- ホワイトリスト管理は管理 Web UI（Basic 認証）のLIFF管理モーダル（👥）から実施

### LINE Bot アクセス制限

`line_handler.py` の `is_allowed_source()` により、`LINE_NOTIFICATION_TARGETS` に登録されていないユーザー・グループからの Bot コマンドは無視する。

- 許可: `LINE_NOTIFICATION_TARGETS` に含まれる userId / groupId
- 不許可: 上記以外（返信なし・HTTP 200 を返す）
- 未設定時: 全許可（開発環境向け）

## API エンドポイント

### 管理 API（Caddy Basic 認証が必要）

| Method | Path | 説明 |
|---|---|---|
| GET | / | 管理 Web UI |
| GET | /health | ヘルスチェック |
| GET | /incidents | インシデント一覧（クエリ: system_name, status, from_date, to_date, limit, offset） |
| GET | /incidents/{id} | インシデント詳細 |
| PUT | /incidents/{id} | 手動更新（ステータス修正等） |
| DELETE | /incidents/{id} | 削除 |
| POST | /sync | 即時メール同期（新規インシデントがあれば LINE 通知） |
| GET | /summary | システム別・ステータス別集計 |
| GET | /members | LIFF許可ユーザー一覧 |
| POST | /members | LIFF許可ユーザー追加 |
| DELETE | /members/{id} | LIFF許可ユーザー削除 |
| GET | /access-log | 403アクセスログ一覧（未登録ユーザーのみ、直近10件） |
| POST | /line/test-notify | LINE テスト通知送信 |

### LIFF API（Caddy 認証なし・LIFF トークン認証）

| Method | Path | 認証 | 説明 |
|---|---|---|---|
| GET | /liff | なし | LIFF Web UI（index.html） |
| GET | /liff/config | なし | `{"liff_id": "..."}` を返す |
| GET | /liff/me | LIFF | ログインユーザー情報（名前・行員コード） |
| GET | /liff/summary | LIFF | システム別・ステータス別集計 |
| GET | /liff/incidents | LIFF | インシデント一覧（同上クエリパラメータ） |
| GET | /liff/incidents/{id} | LIFF | インシデント詳細 |
| PUT | /liff/incidents/{id} | LIFF | ステータス更新等（DELETE は提供しない） |

### Webhook

| Method | Path | 認証 | 説明 |
|---|---|---|---|
| POST | /line/webhook | なし | LINE Messaging API Webhook 受信 |

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

### liff_allowed_users

LIFF UIへのアクセスを許可するユーザーのホワイトリスト。

| カラム | 型 | 説明 |
|---|---|---|
| id | Integer PK | |
| employee_code | String(50) UNIQUE | 行員コード |
| name | String(100) | 氏名 |
| line_user_id | String(100) UNIQUE | LINE ユーザー ID（`U` から始まる） |
| created_at | DateTime | 登録日時 |

管理は Basic 認証付き Web UI のLIFF管理モーダル（👥ボタン）から行う。

### liff_access_logs

LIFF アクセスで 403（未登録）となったユーザーの記録。最大10件。

| カラム | 型 | 説明 |
|---|---|---|
| id | Integer PK | |
| line_user_id | String(100) UNIQUE | LINE ユーザー ID |
| line_display_name | String(200) | LINE 表示名（アクセス時点） |
| accessed_at | DateTime | 最終アクセス日時（再アクセス時に更新） |

同一ユーザーの再アクセスは `accessed_at` と `line_display_name` を更新。10件超えた場合は最古のレコードを削除してから追加。管理 Web UI のLIFF管理モーダルでログ確認・ホワイトリスト登録が可能。

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

# LIFF
LIFF_ID=<LINE Developers Console > LIFF > 追加 で取得した LIFF ID>
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
- **グループ ID**: 下記の手順で取得する

**グループ ID の取得手順:**
1. 対象グループで Bot に何かメッセージを送る
2. `docker compose logs -f trouble-api` でログを確認
   ```
   LINE source: {'type': 'group', 'groupId': 'Cabc123...', 'userId': 'Udef456...'}
   ```
3. `groupId` を `LINE_NOTIFICATION_TARGETS` に追記して再起動

```
LINE_NOTIFICATION_TARGETS=Uxxxxxxxxxxxx          # 個人のみ
LINE_NOTIFICATION_TARGETS=Uxxxxxxxxxxxx,Cxxxxxx  # 個人 + グループ
```

> **注意**: `LINE_NOTIFICATION_TARGETS` は通知先と Bot コマンド許可先を兼ねる。ここに登録されていないソースからのコマンドは `is_allowed_source()` により無視される。

## LIFF 設定

### LINE Developers Console での作業
1. Messaging API チャンネル → **LIFF** タブ → 「追加」
   - Size: `Full`
   - Endpoint URL: `https://forecargo.ngrok.app/trouble/liff`
   - Scope: `profile`
   - Bot link feature: ON（Linked）
2. 登録後に表示される **LIFF ID** を `.env` の `LIFF_ID` に設定
3. `docker compose up -d trouble-api` で再起動

### アクセス制御（ホワイトリスト管理）
LIFF UI は `liff_allowed_users` テーブルで認可制御。

**登録手順（管理 Web UI から）:**
1. `https://forecargo.ngrok.app/trouble/` を Basic 認証でブラウザで開く
2. ヘッダー右の 👥 ボタン → LIFF管理モーダルが開く
3. ユーザーが LIFF URL にアクセスして 403 になると「未登録アクセスログ」に表示される
4. 「登録」ボタンで LINE ID と氏名が入力欄に自動入力 → 行員コードを入力して「追加」

**直接登録（API から）:**
```bash
curl -u ncbtrouble:<パスワード> -X POST https://forecargo.ngrok.app/trouble/members \
  -H "Content-Type: application/json" \
  -d '{"employee_code":"0001","name":"山田 太郎","line_user_id":"Uxxxxxxxxxx"}'
```

### リッチメニュー（チャット下部ボタン）のセットアップ

ホストマシンで一度だけ実行。変更時も再実行すれば上書きされる。

```bash
pip install httpx Pillow
python trouble-api/setup_richmenu.py
```

4ボタン（2×2）。`LIFF_ID` が設定されている場合、発生中・一覧ボタンは LIFF URL を開く URI アクション、同期・ヘルプはメッセージ送信アクション：

| ボタン | LIFF_ID 設定時 | LIFF_ID 未設定時 |
|---|---|---|
| 発生中（左上） | LIFF URL を開く（`?status=発生中` フィルタ付き） | `発生中` を送信 |
| 一覧（右上） | LIFF URL を開く | `一覧` を送信 |
| 同期（左下） | `同期` を送信 | `同期` を送信 |
| ヘルプ（右下） | `ヘルプ` を送信 | `ヘルプ` を送信 |

### Bot コマンド一覧

| コマンド | 説明 |
|---|---|
| 一覧 / リスト | 最新インシデント10件（Flex カルーセル） |
| 発生中 / 障害 | 未解決インシデント（発生中・調査中） |
| #123 | インシデント #123 の詳細 |
| 同期 / sync | メール同期を即時実行、件数を返信 |
| ヘルプ / help | コマンド一覧 |

### Flex Message インシデントカードのデザイン

`line_handler.py` の `make_incident_bubble()` が生成する。

**構造:**
```
┌────────────────────────────┐
│ ▬▬▬▬ (6px ステータス色帯) ▬▬▬ │
│  [発生中] ← ピル形バッジ    │
│  システム名（太字）          │
│  障害種別（グレー）          │
│  ─────────────────────────  │
│  発生          MM/DD HH:MM  │
│  クローズ      MM/DD HH:MM  │
├────────────────────────────┤
│  [■ 詳細を見る  #ID ■]     │ ← 塗りつぶしボタン
└────────────────────────────┘
```

**ステータスカラー:**

| ステータス | アクセント色 | バッジ背景 |
|---|---|---|
| 発生中 | `#DC2626`（赤） | `#FEE2E2` |
| 調査中 | `#D97706`（琥珀） | `#FEF3C7` |
| 復旧済み | `#16A34A`（緑） | `#DCFCE7` |

**「詳細を見る #ID」ボタンの URL:**
- `LIFF_ID` 設定時: `https://liff.line.me/<LIFF_ID>?id=<ID>` → LIFF UIでインシデント詳細が自動表示
- `LIFF_ID` 未設定・`BASE_URL` 設定時: `<BASE_URL>/?id=<ID>` → Basic認証 Web UI
- どちらも未設定: フッターなし（ボタン非表示）

> **注意**: Flex Message のボタン URL は送信時点で固定される。`LIFF_ID` 設定前に送信された通知のボタンは古い URL のままとなる。

## 開発・デバッグポイント

### IMAP 接続・メール既読化

docomoのIMAPサーバーは `imap.spmode.ne.jp:993 (SSL)` を使用。

**メール既読フロー（collector.py）:**
1. INBOX を `readonly=False` で開く（書き込み可能）
2. `UNSEEN`（未読）フラグのメールのみ検索（処理済み = 既読のメールはスキップ）
3. 差出人フィルタ（`SENDER_FILTER`）でマッチしたメールを処理
4. DB commit 成功後、`server.set_flags([uid], [b"\\Seen"])` で既読に変更
5. `ProcessedEmail` による重複チェックでスキップされたメールも同様に既読化

> `processed_emails` テーブルによる重複防止は引き続き有効（`set_flags` 失敗時のフェイルセーフ）。

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
# または Caddy経由（Basic認証付き）
curl -u ncbtrouble:<パスワード> -X POST https://forecargo.ngrok.app/trouble/sync | jq
```

### LINE Webhook 疎通テスト

```bash
# LINE_CHANNEL_SECRET 未設定時は署名検証をスキップ
curl -X POST http://localhost:8002/line/webhook \
  -H "Content-Type: application/json" \
  -d '{"events":[]}'
# → {"status":"ok"}
```

## Basic 認証パスワード変更

1. 新しいハッシュを生成
   ```bash
   docker run --rm caddy:latest caddy hash-password --plaintext "<新しいパスワード>"
   ```
2. `caddy/Caddyfile` の `basic_auth` ブロックを更新
   ```
   basic_auth {
       ncbtrouble <生成したハッシュ>
   }
   ```
3. Caddy を再起動
   ```bash
   docker compose restart caddy
   ```
