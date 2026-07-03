"""transcriber.py（mlx-whisper ラッパ）の単体テスト。"""

import mlx_whisper

import transcriber


def test_forwards_args_and_parses_segments():
    mlx_whisper.transcribe.calls.clear()

    result = transcriber.run_transcription(
        "/tmp/a.wav", model="my-model", language="ja"
    )

    call = mlx_whisper.transcribe.calls[-1]
    assert call["audio"] == "/tmp/a.wav"
    assert call["path_or_hf_repo"] == "my-model"
    assert call["language"] == "ja"

    assert result.model == "my-model"
    assert result.language == "ja"
    assert result.text
    assert result.segments[0].id == 0
    assert result.segments[0].text == "こんにちは"
    assert result.segments[1].text == "世界"


def test_language_none_is_forwarded():
    mlx_whisper.transcribe.calls.clear()

    result = transcriber.run_transcription("/tmp/a.wav", model="m", language=None)

    assert mlx_whisper.transcribe.calls[-1]["language"] is None
    assert result.segments  # スタブは ja として返す
