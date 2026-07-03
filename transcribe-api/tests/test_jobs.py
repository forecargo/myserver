"""jobs.py（ジョブストア + ワーカ）の単体テスト。"""

from datetime import datetime, timedelta

import pytest

from jobs import JobStore, WorkerPool
from models import (
    Diarization,
    DiarizationSegment,
    JobStatus,
    Transcription,
    TranscriptSegment,
)


@pytest.fixture
def store(tmp_path):
    return JobStore(f"sqlite:///{tmp_path}/jobs.db", str(tmp_path))


def _create(store, audio_path="/tmp/a.wav"):
    return store.create(
        audio_filename="a.wav",
        content_type="audio/wav",
        audio_path=audio_path,
        language="ja",
        model="m",
        num_speakers=None,
    ).id


def _make_fns(fail=False):
    def transcribe_fn(path, *, model, language):
        if fail:
            raise ValueError("boom")
        return Transcription(
            model=model,
            language=language or "ja",
            text="hi",
            segments=[TranscriptSegment(id=0, start=0.0, end=1.5, text="hi")],
        )

    def diarize_fn(path, *, num_speakers):
        return Diarization(
            model="d",
            num_speakers=1,
            segments=[DiarizationSegment(start=0.0, end=1.5, speaker="SPEAKER_00")],
        )

    return transcribe_fn, diarize_fn


def test_create_is_queued(store):
    job_id = _create(store)
    assert store.get(job_id).status == JobStatus.queued.value


def test_process_completes(store):
    transcribe_fn, diarize_fn = _make_fns()
    pool = WorkerPool(
        store, transcribe_fn=transcribe_fn, diarize_fn=diarize_fn, concurrency=0
    )
    job_id = _create(store)

    pool.process(job_id)

    row = store.get(job_id)
    assert row.status == JobStatus.completed.value
    result = store.to_result(row)
    assert result.transcription.segments[0].text == "hi"
    assert result.diarization.segments[0].speaker == "SPEAKER_00"
    assert result.audio.duration_sec == 1.5
    assert result.completed_at is not None


def test_process_failure_records_error(store):
    transcribe_fn, diarize_fn = _make_fns(fail=True)
    pool = WorkerPool(
        store, transcribe_fn=transcribe_fn, diarize_fn=diarize_fn, concurrency=0
    )
    job_id = _create(store)

    pool.process(job_id)

    row = store.get(job_id)
    assert row.status == JobStatus.failed.value
    assert "boom" in row.error


def test_persistence_across_instances(tmp_path):
    url = f"sqlite:///{tmp_path}/jobs.db"
    store1 = JobStore(url, str(tmp_path))
    job_id = _create(store1)

    store2 = JobStore(url, str(tmp_path))
    assert store2.get(job_id) is not None
    assert store2.get(job_id).status == JobStatus.queued.value


def test_worker_processes_all_sequentially(store):
    transcribe_fn, diarize_fn = _make_fns()
    pool = WorkerPool(
        store, transcribe_fn=transcribe_fn, diarize_fn=diarize_fn, concurrency=1
    )
    pool.start()
    job_ids = [_create(store) for _ in range(3)]
    for job_id in job_ids:
        pool.submit(job_id)
    pool.stop()

    for job_id in job_ids:
        assert store.get(job_id).status == JobStatus.completed.value


def test_delete_removes_job_and_file(store, tmp_path):
    audio = tmp_path / "x.wav"
    audio.write_bytes(b"x")
    job_id = _create(store, audio_path=str(audio))

    assert store.delete(job_id) is True
    assert store.get(job_id) is None
    assert not audio.exists()
    # 二重削除は False
    assert store.delete(job_id) is False


def test_cleanup_expired(store, tmp_path):
    audio = tmp_path / "y.wav"
    audio.write_bytes(b"y")
    job_id = _create(store, audio_path=str(audio))

    future = datetime.now().astimezone() + timedelta(hours=2)
    removed = store.cleanup_expired(retention_hours=1, now=future)

    assert removed == 1
    assert store.get(job_id) is None
    assert not audio.exists()


def test_cleanup_keeps_recent(store):
    job_id = _create(store)
    removed = store.cleanup_expired(retention_hours=24)
    assert removed == 0
    assert store.get(job_id) is not None
