"""pyannote.audio による話者分離のラッパ。"""

import logging

import torch
import torchaudio
from pyannote.audio import Pipeline

from models import Diarization, DiarizationSegment

logger = logging.getLogger("transcribe-api")


def resolve_device(device: str = "auto") -> torch.device:
    """使用するデバイスを解決する。

    "auto" の場合は Metal(MPS) → CUDA → CPU の順で利用可能なものを選ぶ。
    """
    if device and device != "auto":
        return torch.device(device)
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def load_pipeline(model: str, hf_token: str, device: str = "auto"):
    """話者分離パイプラインをロードする（起動時に一度だけ呼ぶ）。

    Args:
        model: pyannote のモデル名(HF repo)。
        hf_token: HuggingFace アクセストークン。
        device: "auto"/"mps"/"cuda"/"cpu"。既定は auto（GPU 優先）。

    Returns:
        指定デバイスへ移動済みのパイプライン。
    """
    pipeline = Pipeline.from_pretrained(model, token=hf_token)
    dev = resolve_device(device)
    pipeline.to(dev)
    logger.info("pyannote pipeline loaded on device=%s", dev)
    return pipeline


def run_diarization(
    pipeline, audio_path: str, *, model: str, num_speakers: int | None = None
) -> Diarization:
    """音声を話者分離して Diarization を返す。

    Args:
        pipeline: `load_pipeline` で得たパイプライン。
        audio_path: 音声ファイルのパス。
        model: 記録用のモデル名。
        num_speakers: 話者数が既知の場合のヒント。

    Returns:
        話者分離結果。
    """
    # ファイル読込時のデコーダ由来のサンプル数不一致
    # (例: "resulted in N samples instead of expected M") を避けるため、
    # 波形をメモリに読み込んで dict で渡す。
    waveform, sample_rate = torchaudio.load(audio_path)
    payload = {"waveform": waveform, "sample_rate": sample_rate}

    kwargs: dict = {}
    if num_speakers:
        kwargs["num_speakers"] = num_speakers
    result = pipeline(payload, **kwargs)
    # pyannote 4.x は DiarizeOutput(.speaker_diarization) を、
    # 3.x は Annotation を直接返す。両対応で正規化する。
    annotation = getattr(result, "speaker_diarization", result)

    segments: list[DiarizationSegment] = []
    speakers: set[str] = set()
    for turn, _, speaker in annotation.itertracks(yield_label=True):
        segments.append(
            DiarizationSegment(
                start=float(turn.start), end=float(turn.end), speaker=str(speaker)
            )
        )
        speakers.add(speaker)

    return Diarization(model=model, num_speakers=len(speakers), segments=segments)
