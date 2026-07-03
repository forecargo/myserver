# transcribe-api — テスト計画書 (TESTPLAN)

[SPEC.md](./SPEC.md) の要件に対するテスト計画。実装着手前に「何を・どのレベルで・どうやって」検証するかを定義する。

---

## 1. 方針

- **重い/Apple依存の実体はスタブ化**: `mlx-whisper`・`pyannote.audio`・`torch` は CI や非 Apple Silicon 環境でロードできないため、`conftest.py` で `sys.modules` にフェイクモジュールを注入し、モデル本体をロードせずにテストする（trouble-api 流儀）。
- **3層構成**:
  1. **単体テスト**（Unit） — 各モジュールの純粋ロジック。スタブ利用・高速・CI 対象。
  2. **統合テスト**（Integration） — FastAPI `TestClient` によるエンドポイント検証。ワーカ/モデルはスタブ。CI 対象。
  3. **手動 E2E**（Manual） — 実モデル + 実音声で Apple Silicon ホスト上で実施。CI 対象外・リリース前チェックリスト。
- **カバレッジ目標**: Unit + Integration で分岐カバレッジ 80% 以上（`pytest --cov`）。
- **CI 制約**: Unit/Integration のみ自動化。実モデルを要する E2E は手動。

---

## 2. テスト環境・ツール

| 項目 | 内容 |
| --- | --- |
| ランナー | `pytest`（`uv run pytest`） |
| HTTP | `fastapi.testclient.TestClient` |
| カバレッジ | `pytest-cov` |
| スタブ | `sys.modules` 注入（`conftest.py`）+ `monkeypatch` |
| DB | `sqlite:///:memory:`（`DATABASE_URL` を環境変数で上書き） |
| フィクスチャ音声 | `tests/fixtures/` に極小 wav（数百ms）を1つ配置。単体では実デコードせずパスのみ利用 |

### conftest.py で行う準備
- プロジェクトルートを `sys.path` に追加。
- テスト用環境変数を `os.environ.setdefault` で設定（`HF_TOKEN=dummy`, `DATABASE_URL=sqlite:///:memory:`, `WORK_DIR=<tmp>`）。
- `mlx_whisper`・`pyannote.audio` のフェイクモジュールを `sys.modules` に注入（アプリ import より前）。

---

## 3. 単体テスト（Unit）

### 3.1 config.py
- [ ] 各環境変数の既定値が正しく解決される（`WHISPER_MODEL`, `WHISPER_LANGUAGE=ja`, `PORT=8007` 等）。
- [ ] `MAX_UPLOAD_MB` / `WORKER_CONCURRENCY` / `JOB_RETENTION_HOURS` が `int` にパースされる。
- [ ] **`HF_TOKEN` 未設定で `RuntimeError`（fail-fast）** が送出される。
- [ ] 環境変数で既定値を上書きできる。

### 3.2 models.py（Pydantic）
- [ ] 結果スキーマ（§5）が期待通りシリアライズされる（`transcription` / `diarization` が別配列で保持される）。
- [ ] `status` の enum 値（`queued|processing|completed|failed`）を検証。
- [ ] `failed` 時に `error` を保持できる。必須/任意フィールドのバリデーション。

### 3.3 transcriber.py（mlx-whisper ラッパ、スタブ）
- [ ] フェイク `mlx_whisper.transcribe` が期待引数（`path`, `language`, `model`）で呼ばれる。
- [ ] 返却 dict を `segments`（`id/start/end/text`）+ 全文 `text` に正しく整形する。
- [ ] `language` 未指定時に既定（`ja`）が適用される。

### 3.4 diarizer.py（pyannote ラッパ、スタブ）
- [ ] フェイク Pipeline が `HF_TOKEN` 付きでロードされる。
- [ ] Annotation 相当の戻り値を `segments`（`start/end/speaker`）へ整形する。
- [ ] `num_speakers` ヒント指定時に Pipeline へ渡される。
- [ ] `num_speakers` から結果の話者数を集計できる。

### 3.5 jobs.py（ジョブストア + ワーカ）
- [ ] ジョブ登録で `queued` として永続化される。
- [ ] **状態遷移**: `queued → processing → completed`（正常系）。
- [ ] **失敗系**: ワーカ内で例外 → `failed` + `error` が記録される（後続ジョブは継続）。
- [ ] SQLite 永続化: 別コネクション/再オープンでジョブが復元できる（**プロセス再起動耐性**）。
- [ ] `WORKER_CONCURRENCY=1` で逐次処理されること（並列に走らない）。
- [ ] 保持期限クリーンアップ: `JOB_RETENTION_HOURS` 超過ジョブと成果物ファイルが削除される（時刻は注入して検証）。

---

## 4. 統合テスト（Integration / TestClient）

ワーカとモデルはスタブし、エンドポイントの契約を検証する。

### 4.1 POST /jobs
- [ ] 正常: 許可 content-type の音声 → `202` + `{ job_id, status:"queued", created_at }`。
- [ ] バリデーション: 非対応 content-type → `400`（日本語 detail）。
- [ ] バリデーション: 拡張子不一致 → `400`。
- [ ] バリデーション: `MAX_UPLOAD_MB` 超過 → `413`（または `400`）。
- [ ] `file` 欠如 → `422`。
- [ ] 任意パラメータ `language` / `model` / `num_speakers` がジョブに反映される。
- [ ] 受付時に音声が `WORK_DIR` に保存される。

### 4.2 GET /jobs/{job_id}
- [ ] `queued` / `processing` / `completed` / `failed` の各状態を返す。
- [ ] `completed` 時に結果スキーマ（§5）を含む。
- [ ] `failed` 時に `error` を含む。
- [ ] 未知の `job_id` → `404`。

### 4.3 GET /jobs/{job_id}/result
- [ ] 完了済み → 結果スキーマを返す。
- [ ] 未完了（queued/processing）→ `409`。
- [ ] 未知の `job_id` → `404`。

### 4.4 GET /jobs（一覧・任意）
- [ ] `limit` / `offset` によるページングが機能する。

### 4.5 DELETE /jobs/{job_id}（任意）
- [ ] ジョブ + 成果物（音声・結果）が削除される。
- [ ] 削除後の取得 → `404`。

### 4.6 GET /health
- [ ] `{ status:"ok", models_loaded: <bool> }` を返す。

### 4.7 起動シーケンス（lifespan）
- [ ] スタブモデルが起動時に一度だけロードされ `app.state` に保持される。
- [ ] `HF_TOKEN` 未設定での起動が fail-fast する（アプリ生成が失敗する）。

---

## 5. 手動 E2E（Apple Silicon ホスト・実モデル）

CI 対象外。リリース前チェックリストとして実施。

- [ ] `uv sync` 後、`scripts/run.sh` でサーバが起動しモデルがロードされる。
- [ ] 短い日本語音声（wav, 10〜30秒, 2話者）を `POST /jobs` → `202`。
- [ ] ポーリングで `completed` になり、`transcription.text` が妥当・`diarization.segments` に複数話者（`SPEAKER_00/01`）が現れる。
- [ ] 長尺音声（数分）でタイムアウトせず完了する。
- [ ] 各種フォーマット（wav / mp3 / m4a / flac）が処理できる。
- [ ] `language=auto` で言語自動判定が機能する。
- [ ] Caddy 経由（`/transcribe*` → `host.docker.internal:8007`）で疎通する。
- [ ] `JOB_RETENTION_HOURS` 経過後に成果物が自動削除される。
- [ ] **ログに文字起こし本文・音声内容が出力されていない**こと（個人情報保護の確認）。

---

## 6. 非機能・セキュリティ確認

- [ ] 個人情報: 成果物の自動削除とログ非出力（§5 の E2E 項目で確認）。
- [ ] 異常系: 破損音声・空ファイル・0 バイトで `failed` になりサーバが落ちない。
- [ ] 同時投入: 複数ジョブ投入時、ワーカが逐次処理しつつ受付は即応答する（GPU 逐次の担保）。
- [ ] リソース: 大容量アップロード時にメモリが枯渇しない（ストリーミング保存の確認）。

---

## 7. テストディレクトリ構成（予定）

```
transcribe-api/tests/
  __init__.py
  conftest.py            # sys.modules スタブ, 環境変数, tmp WORK_DIR, TestClient fixture
  fixtures/
    tiny.wav             # 極小サンプル音声
  test_config.py         # §3.1
  test_models.py         # §3.2
  test_transcriber.py    # §3.3
  test_diarizer.py       # §3.4
  test_jobs.py           # §3.5
  test_api.py            # §4（TestClient）
```

---

## 8. 実行コマンド

```bash
cd transcribe-api
uv run pytest                     # 全 Unit + Integration
uv run pytest -k jobs             # ジョブ関連のみ
uv run pytest --cov --cov-report=term-missing
```

---

## 9. スコープ外（本計画では扱わない）

- 実モデルの精度（WER / DER）評価 — 別途モデル評価タスクとする。
- 負荷試験（大量同時接続） — 必要になった段階で計画。
- SRT/VTT 出力・SSE 進捗など将来拡張（SPEC §11）。
