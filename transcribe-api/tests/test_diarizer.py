"""diarizer.py（pyannote.audio ラッパ）の単体テスト。"""

import diarizer


def test_load_pipeline_passes_token():
    pipeline = diarizer.load_pipeline("pyannote/x", "tok-123")
    assert pipeline.model == "pyannote/x"
    assert pipeline.token == "tok-123"


def test_run_diarization_with_num_speakers():
    pipeline = diarizer.load_pipeline("pyannote/x", "tok")

    result = diarizer.run_diarization(
        pipeline, "/tmp/a.wav", model="pyannote/x", num_speakers=2
    )

    assert pipeline.last_num_speakers == 2
    assert result.model == "pyannote/x"
    assert result.num_speakers == 2
    assert {s.speaker for s in result.segments} == {"SPEAKER_00", "SPEAKER_01"}


def test_run_diarization_without_num_speakers():
    pipeline = diarizer.load_pipeline("m", "t")

    result = diarizer.run_diarization(pipeline, "/tmp/a.wav", model="m")

    assert pipeline.last_num_speakers is None
    assert len(result.segments) == 2
