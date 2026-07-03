"""config.py の単体テスト。"""

import pytest

import config

_INT_KEYS = [
    "PORT",
    "MAX_UPLOAD_MB",
    "WORKER_CONCURRENCY",
    "JOB_RETENTION_HOURS",
]
_STR_KEYS = [
    "WHISPER_MODEL",
    "WHISPER_LANGUAGE",
    "DIARIZATION_MODEL",
    "DATABASE_URL",
]


def test_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("WORK_DIR", str(tmp_path))
    monkeypatch.setenv("HF_TOKEN", "x")
    for key in _INT_KEYS + _STR_KEYS:
        monkeypatch.delenv(key, raising=False)

    settings = config.load_settings()

    assert settings.whisper_model == "mlx-community/whisper-large-v3-mlx"
    assert settings.whisper_language == "ja"
    assert settings.diarization_model == "pyannote/speaker-diarization-3.1"
    assert settings.port == 8007
    assert settings.max_upload_mb == 500
    assert settings.worker_concurrency == 1
    assert settings.job_retention_hours == 24
    assert settings.database_url == f"sqlite:///{tmp_path}/jobs.db"


def test_int_parsing(monkeypatch, tmp_path):
    monkeypatch.setenv("WORK_DIR", str(tmp_path))
    monkeypatch.setenv("MAX_UPLOAD_MB", "10")
    monkeypatch.setenv("WORKER_CONCURRENCY", "3")
    monkeypatch.setenv("JOB_RETENTION_HOURS", "48")

    settings = config.load_settings()

    assert settings.max_upload_mb == 10
    assert settings.worker_concurrency == 3
    assert settings.job_retention_hours == 48


def test_hf_token_fail_fast(monkeypatch, tmp_path):
    monkeypatch.setenv("WORK_DIR", str(tmp_path))
    monkeypatch.delenv("HF_TOKEN", raising=False)

    settings = config.load_settings()

    with pytest.raises(RuntimeError):
        config.validate_settings(settings)


def test_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("WORK_DIR", str(tmp_path))
    monkeypatch.setenv("WHISPER_MODEL", "custom-model")
    monkeypatch.setenv("WHISPER_LANGUAGE", "en")

    settings = config.load_settings()

    assert settings.whisper_model == "custom-model"
    assert settings.whisper_language == "en"
