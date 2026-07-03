"""環境変数から設定を読み込むモジュール。

設定値は `load_settings()` で読み込む。`HF_TOKEN` の必須チェックは
`validate_settings()` で行い、アプリ起動時(lifespan)に fail-fast させる。
"""

import os
from dataclasses import dataclass

DEFAULT_WHISPER_MODEL = "mlx-community/whisper-large-v3-mlx"
DEFAULT_WHISPER_LANGUAGE = "ja"
DEFAULT_DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"
DEFAULT_PYANNOTE_DEVICE = "auto"
DEFAULT_PORT = 8007
DEFAULT_WORK_DIR = "./work"
DEFAULT_MAX_UPLOAD_MB = 500
DEFAULT_WORKER_CONCURRENCY = 1
DEFAULT_JOB_RETENTION_HOURS = 24


@dataclass(frozen=True)
class Settings:
    """アプリ全体の設定値。"""

    whisper_model: str
    whisper_language: str
    hf_token: str
    diarization_model: str
    pyannote_device: str
    port: int
    work_dir: str
    database_url: str
    max_upload_mb: int
    worker_concurrency: int
    job_retention_hours: int


def _get_int(name: str, default: int) -> int:
    """環境変数を int として取得する（未設定・空なら default）。"""
    raw = os.getenv(name, "")
    return int(raw) if raw else default


def load_settings() -> Settings:
    """現在の環境変数から Settings を生成する。"""
    work_dir = os.getenv("WORK_DIR", DEFAULT_WORK_DIR)
    default_db = f"sqlite:///{work_dir}/jobs.db"
    return Settings(
        whisper_model=os.getenv("WHISPER_MODEL", DEFAULT_WHISPER_MODEL),
        whisper_language=os.getenv("WHISPER_LANGUAGE", DEFAULT_WHISPER_LANGUAGE),
        hf_token=os.getenv("HF_TOKEN", ""),
        diarization_model=os.getenv("DIARIZATION_MODEL", DEFAULT_DIARIZATION_MODEL),
        pyannote_device=os.getenv("PYANNOTE_DEVICE", DEFAULT_PYANNOTE_DEVICE),
        port=_get_int("PORT", DEFAULT_PORT),
        work_dir=work_dir,
        database_url=os.getenv("DATABASE_URL", default_db),
        max_upload_mb=_get_int("MAX_UPLOAD_MB", DEFAULT_MAX_UPLOAD_MB),
        worker_concurrency=_get_int("WORKER_CONCURRENCY", DEFAULT_WORKER_CONCURRENCY),
        job_retention_hours=_get_int("JOB_RETENTION_HOURS", DEFAULT_JOB_RETENTION_HOURS),
    )


def validate_settings(settings: Settings) -> None:
    """必須設定を検証する。未設定なら RuntimeError（fail-fast）。"""
    if not settings.hf_token:
        raise RuntimeError(
            "HF_TOKEN が設定されていません。pyannote モデル利用のため "
            "HuggingFace アクセストークンを環境変数 HF_TOKEN に設定してください。"
        )
