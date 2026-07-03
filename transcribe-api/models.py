"""API リクエスト/レスポンスの Pydantic スキーマ定義。

文字起こし結果(transcription)と話者分離結果(diarization)は突合せず、
それぞれ別配列で保持する「分離形式」。
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(str, Enum):
    """ジョブの状態。"""

    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class AudioInfo(BaseModel):
    """入力音声のメタ情報。"""

    filename: str
    content_type: str
    duration_sec: float | None = None


class TranscriptSegment(BaseModel):
    """文字起こしの1セグメント。"""

    id: int
    start: float
    end: float
    text: str


class Transcription(BaseModel):
    """文字起こし結果（mlx-whisper）。"""

    model_config = ConfigDict(protected_namespaces=())

    model: str
    language: str
    text: str
    segments: list[TranscriptSegment] = Field(default_factory=list)


class DiarizationSegment(BaseModel):
    """話者分離の1区間。"""

    start: float
    end: float
    speaker: str


class Diarization(BaseModel):
    """話者分離結果（pyannote.audio）。"""

    model_config = ConfigDict(protected_namespaces=())

    model: str
    num_speakers: int
    segments: list[DiarizationSegment] = Field(default_factory=list)


class JobAccepted(BaseModel):
    """POST /jobs の受付応答。"""

    job_id: str
    status: JobStatus
    created_at: str


class JobResult(BaseModel):
    """ジョブ状態 + 結果（分離形式）。"""

    job_id: str
    status: JobStatus
    audio: AudioInfo | None = None
    transcription: Transcription | None = None
    diarization: Diarization | None = None
    error: str | None = None
    created_at: str
    completed_at: str | None = None


class HealthResponse(BaseModel):
    """GET /health の応答。"""

    status: str
    models_loaded: bool
