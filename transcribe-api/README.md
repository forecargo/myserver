# transcribe-api

音声ファイルを受け取り、**mlx-whisper による文字起こし**と **pyannote.audio による話者分離**の結果を返す非同期 API。

- 要件定義 → [SPEC.md](./SPEC.md)
- テスト計画 → [TESTPLAN.md](./TESTPLAN.md)

## 前提条件

- **Apple Silicon (Metal) 必須**（mlx-whisper が依存）。Docker 非対応、macOS ホスト上で native 実行。
- HuggingFace アクセストークン（`HF_TOKEN`）。`pyannote/speaker-diarization-3.1` の利用規約への同意が必要。

## セットアップ

```bash
cd transcribe-api
cp .env.example .env   # HF_TOKEN を設定
uv venv
uv sync
```

## 起動

```bash
./scripts/run.sh        # uv run uvicorn main:app --port 8007
```

## 使い方（非同期ジョブ）

```bash
# 1. 音声を投げてジョブを受け付けさせる
curl -sF file=@meeting.wav http://localhost:8007/jobs
# => {"job_id":"...","status":"queued","created_at":"..."}

# 2. 状態をポーリング（completed で結果が入る）
curl -s http://localhost:8007/jobs/<job_id>
```

結果は `transcription`（文字起こしセグメント）と `diarization`（話者区間）を**別々に**返す。詳細は [SPEC.md](./SPEC.md) 参照。

## テスト

```bash
uv run pytest
uv run pytest --cov --cov-report=term-missing
```

`mlx-whisper` / `pyannote.audio` は `tests/conftest.py` でスタブ化しているため、非 Apple Silicon 環境でもテストは実行できる。
