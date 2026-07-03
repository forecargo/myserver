"""テスト共通設定。

`mlx_whisper` / `pyannote.audio` は重く Apple Silicon 依存のため、
アプリ本体を import する前に `sys.modules` へフェイクを注入して
モデルをロードせずにテストできるようにする。
"""

import io
import sys
import types
import wave
from pathlib import Path

import pytest

# プロジェクトルートを import パスへ追加
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 既定の環境変数（各テストで monkeypatch により上書き可）
import os  # noqa: E402

os.environ.setdefault("HF_TOKEN", "dummy-token")
os.environ.setdefault("WORKER_CONCURRENCY", "0")


def _install_mlx_whisper_stub() -> None:
    module = types.ModuleType("mlx_whisper")

    def transcribe(audio, *, path_or_hf_repo=None, language=None, **kwargs):
        transcribe.calls.append(
            {
                "audio": audio,
                "path_or_hf_repo": path_or_hf_repo,
                "language": language,
            }
        )
        return {
            "text": "こんにちは 世界",
            "language": language or "ja",
            "segments": [
                {"id": 0, "start": 0.0, "end": 1.5, "text": "こんにちは"},
                {"id": 1, "start": 1.5, "end": 3.0, "text": "世界"},
            ],
        }

    transcribe.calls = []
    module.transcribe = transcribe
    sys.modules["mlx_whisper"] = module


def _install_pyannote_stub() -> None:
    pyannote = types.ModuleType("pyannote")
    audio = types.ModuleType("pyannote.audio")

    class _Turn:
        def __init__(self, start: float, end: float) -> None:
            self.start = start
            self.end = end

    class _Annotation:
        def __init__(self, tracks):
            self._tracks = tracks

        def itertracks(self, yield_label: bool = False):
            for start, end, speaker in self._tracks:
                if yield_label:
                    yield _Turn(start, end), None, speaker
                else:
                    yield _Turn(start, end), None

    class Pipeline:
        @classmethod
        def from_pretrained(cls, model, token=None, **kwargs):
            inst = cls()
            inst.model = model
            inst.token = token
            inst.last_num_speakers = None
            return inst

        def to(self, device):
            self.device = device
            return self

        def __call__(self, audio, num_speakers=None, **kwargs):
            self.last_num_speakers = num_speakers
            return _Annotation(
                [
                    (0.0, 1.5, "SPEAKER_00"),
                    (1.5, 3.0, "SPEAKER_01"),
                ]
            )

    audio.Pipeline = Pipeline
    pyannote.audio = audio
    sys.modules["pyannote"] = pyannote
    sys.modules["pyannote.audio"] = audio


def _install_torchaudio_stub() -> None:
    module = types.ModuleType("torchaudio")

    def load(path, **kwargs):
        # 波形はフェイク Pipeline が無視するのでダミーで良い
        return ("WAVEFORM", 16000)

    module.load = load
    sys.modules["torchaudio"] = module


_install_mlx_whisper_stub()
_install_pyannote_stub()
_install_torchaudio_stub()


@pytest.fixture
def wav_bytes() -> bytes:
    """アップロード用の極小 WAV バイト列。"""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 1600)
    return buf.getvalue()


@pytest.fixture
def work_dir(tmp_path, monkeypatch):
    """テスト毎に隔離した作業ディレクトリ + DB を設定する。"""
    d = tmp_path / "work"
    d.mkdir()
    monkeypatch.setenv("WORK_DIR", str(d))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{d}/jobs.db")
    monkeypatch.setenv("WORKER_CONCURRENCY", "0")
    return d
