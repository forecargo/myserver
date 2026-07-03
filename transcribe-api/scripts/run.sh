#!/usr/bin/env bash
set -euo pipefail

# transcribe-api を macOS ホスト上で native 起動する。
cd "$(dirname "$0")/.."

# .env があれば読み込む（HF_TOKEN 等）
if [[ -f .env ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

# MPS 未対応の演算のみ CPU にフォールバックさせる（pyannote 対策）
export PYTORCH_ENABLE_MPS_FALLBACK="${PYTORCH_ENABLE_MPS_FALLBACK:-1}"

exec uv run uvicorn main:app --host 0.0.0.0 --port "${PORT:-8007}"
