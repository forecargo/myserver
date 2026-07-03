"""mlx-whisper による文字起こしのラッパ。"""

import mlx_whisper

from models import Transcription, TranscriptSegment


def run_transcription(
    audio_path: str, *, model: str, language: str | None
) -> Transcription:
    """音声を文字起こしして Transcription を返す。

    Args:
        audio_path: 音声ファイルのパス。
        model: mlx-whisper のモデル名(HF repo)。
        language: 文字起こし言語。None の場合は自動判定。

    Returns:
        文字起こし結果。
    """
    result = mlx_whisper.transcribe(
        audio_path, path_or_hf_repo=model, language=language
    )
    segments = [
        TranscriptSegment(
            id=int(seg.get("id", index)),
            start=float(seg["start"]),
            end=float(seg["end"]),
            text=str(seg.get("text", "")).strip(),
        )
        for index, seg in enumerate(result.get("segments", []))
    ]
    return Transcription(
        model=model,
        language=result.get("language") or (language or ""),
        text=str(result.get("text", "")).strip(),
        segments=segments,
    )
