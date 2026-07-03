"""main.py（FastAPI エンドポイント）の統合テスト。

WORKER_CONCURRENCY=0（conftest の work_dir fixture）でワーカを止め、
状態依存の検証はストアを直接操作して決定的に行う。
"""

import pytest
from fastapi.testclient import TestClient

from models import (
    AudioInfo,
    Diarization,
    DiarizationSegment,
    Transcription,
    TranscriptSegment,
)


@pytest.fixture
def client(work_dir):
    import main

    with TestClient(main.app) as test_client:
        yield test_client, main


def _create_queued(main_module):
    return main_module.app.state.store.create(
        audio_filename="a.wav",
        content_type="audio/wav",
        audio_path="/tmp/a.wav",
        language="ja",
        model="m",
        num_speakers=None,
    ).id


def _complete(main_module, job_id):
    main_module.app.state.store.mark_completed(
        job_id,
        audio=AudioInfo(filename="a.wav", content_type="audio/wav", duration_sec=1.5),
        transcription=Transcription(
            model="m",
            language="ja",
            text="hi",
            segments=[TranscriptSegment(id=0, start=0.0, end=1.5, text="hi")],
        ),
        diarization=Diarization(
            model="d",
            num_speakers=1,
            segments=[DiarizationSegment(start=0.0, end=1.5, speaker="SPEAKER_00")],
        ),
    )


def test_health(client):
    test_client, _ = client
    resp = test_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "models_loaded": True}


def test_post_jobs_accepts_audio(client, wav_bytes):
    test_client, _ = client
    resp = test_client.post(
        "/jobs", files={"file": ("test.wav", wav_bytes, "audio/wav")}
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "queued"
    assert body["job_id"]
    assert body["created_at"]


def test_post_jobs_rejects_bad_content_type(client):
    test_client, _ = client
    resp = test_client.post(
        "/jobs", files={"file": ("test.txt", b"hello", "text/plain")}
    )
    assert resp.status_code == 400


def test_post_jobs_rejects_extension_mismatch(client, wav_bytes):
    test_client, _ = client
    resp = test_client.post(
        "/jobs", files={"file": ("test.mp3", wav_bytes, "audio/wav")}
    )
    assert resp.status_code == 400


def test_post_jobs_missing_file(client):
    test_client, _ = client
    resp = test_client.post("/jobs", data={})
    assert resp.status_code == 422


def test_post_jobs_too_large(work_dir, wav_bytes, monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "0")
    import main

    with TestClient(main.app) as test_client:
        resp = test_client.post(
            "/jobs", files={"file": ("test.wav", wav_bytes, "audio/wav")}
        )
    assert resp.status_code == 413


def test_get_job_completed(client):
    test_client, main_module = client
    job_id = _create_queued(main_module)
    _complete(main_module, job_id)

    resp = test_client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["transcription"]["segments"][0]["text"] == "hi"
    assert body["diarization"]["num_speakers"] == 1
    assert body["audio"]["duration_sec"] == 1.5


def test_get_job_not_found(client):
    test_client, _ = client
    assert test_client.get("/jobs/does-not-exist").status_code == 404


def test_result_conflict_when_incomplete(client):
    test_client, main_module = client
    job_id = _create_queued(main_module)
    resp = test_client.get(f"/jobs/{job_id}/result")
    assert resp.status_code == 409


def test_result_ok_when_completed(client):
    test_client, main_module = client
    job_id = _create_queued(main_module)
    _complete(main_module, job_id)
    resp = test_client.get(f"/jobs/{job_id}/result")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_result_not_found(client):
    test_client, _ = client
    assert test_client.get("/jobs/nope/result").status_code == 404


def test_delete_job(client):
    test_client, main_module = client
    job_id = _create_queued(main_module)
    assert test_client.delete(f"/jobs/{job_id}").status_code == 204
    assert test_client.get(f"/jobs/{job_id}").status_code == 404
    assert test_client.delete(f"/jobs/{job_id}").status_code == 404


def test_list_jobs_pagination(client):
    test_client, main_module = client
    for _ in range(3):
        _create_queued(main_module)
    resp = test_client.get("/jobs", params={"limit": 2})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_startup_fails_without_hf_token(work_dir, monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    import main

    with pytest.raises(RuntimeError):
        with TestClient(main.app):
            pass
