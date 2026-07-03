"""models.py（Pydantic スキーマ）の単体テスト。"""

from models import (
    AudioInfo,
    Diarization,
    DiarizationSegment,
    JobResult,
    JobStatus,
    Transcription,
    TranscriptSegment,
)


def test_result_serialization_separates_transcription_and_diarization():
    result = JobResult(
        job_id="j1",
        status=JobStatus.completed,
        audio=AudioInfo(filename="a.wav", content_type="audio/wav", duration_sec=3.0),
        transcription=Transcription(
            model="m",
            language="ja",
            text="こんにちは",
            segments=[TranscriptSegment(id=0, start=0.0, end=1.5, text="こんにちは")],
        ),
        diarization=Diarization(
            model="d",
            num_speakers=2,
            segments=[DiarizationSegment(start=0.0, end=1.5, speaker="SPEAKER_00")],
        ),
        created_at="t0",
        completed_at="t1",
    )

    data = result.model_dump()

    assert data["transcription"]["segments"][0]["text"] == "こんにちは"
    assert data["diarization"]["segments"][0]["speaker"] == "SPEAKER_00"
    # 分離形式: transcription と diarization は独立キー
    assert "transcription" in data and "diarization" in data


def test_failed_result_holds_error():
    result = JobResult(
        job_id="j2", status=JobStatus.failed, error="boom", created_at="t0"
    )
    assert result.status is JobStatus.failed
    assert result.error == "boom"
    assert result.transcription is None
    assert result.diarization is None


def test_status_enum_values():
    assert {s.value for s in JobStatus} == {
        "queued",
        "processing",
        "completed",
        "failed",
    }
