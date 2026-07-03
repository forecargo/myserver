"""ジョブの永続化(SQLite)とバックグラウンドワーカ。"""

import json
import queue
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

from sqlalchemy import Integer, String, Text, create_engine, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)

from models import (
    AudioInfo,
    Diarization,
    JobResult,
    JobStatus,
    Transcription,
)


class Base(DeclarativeBase):
    pass


class Job(Base):
    """ジョブの永続化テーブル。"""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[str] = mapped_column(String)
    completed_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_filename: Mapped[str] = mapped_column(String)
    audio_content_type: Mapped[str] = mapped_column(String)
    audio_path: Mapped[str] = mapped_column(String)
    language: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    num_speakers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


@dataclass
class JobRow:
    """スレッド跨ぎで安全に扱うためのジョブのスナップショット。"""

    id: str
    status: str
    created_at: str
    completed_at: Optional[str]
    error: Optional[str]
    audio_filename: str
    audio_content_type: str
    audio_path: str
    language: Optional[str]
    model: Optional[str]
    num_speakers: Optional[int]
    result_json: Optional[str]


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def _to_row(job: Job) -> JobRow:
    return JobRow(
        id=job.id,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error=job.error,
        audio_filename=job.audio_filename,
        audio_content_type=job.audio_content_type,
        audio_path=job.audio_path,
        language=job.language,
        model=job.model,
        num_speakers=job.num_speakers,
        result_json=job.result_json,
    )


class JobStore:
    """ジョブの CRUD と結果永続化を担う。"""

    def __init__(self, database_url: str, work_dir: str) -> None:
        connect_args = (
            {"check_same_thread": False}
            if database_url.startswith("sqlite")
            else {}
        )
        self.engine = create_engine(database_url, connect_args=connect_args)
        self.work_dir = Path(work_dir)
        Base.metadata.create_all(self.engine)
        self._Session = sessionmaker(self.engine, expire_on_commit=False)

    def create(
        self,
        *,
        audio_filename: str,
        content_type: str,
        audio_path: str,
        language: Optional[str] = None,
        model: Optional[str] = None,
        num_speakers: Optional[int] = None,
        job_id: Optional[str] = None,
    ) -> JobRow:
        """ジョブを queued 状態で登録する。"""
        job_id = job_id or uuid.uuid4().hex
        with self._Session() as session:
            job = Job(
                id=job_id,
                status=JobStatus.queued.value,
                created_at=_now_iso(),
                completed_at=None,
                error=None,
                audio_filename=audio_filename,
                audio_content_type=content_type,
                audio_path=audio_path,
                language=language,
                model=model,
                num_speakers=num_speakers,
                result_json=None,
            )
            session.add(job)
            session.commit()
            return _to_row(job)

    def get(self, job_id: str) -> Optional[JobRow]:
        with self._Session() as session:
            job = session.get(Job, job_id)
            return _to_row(job) if job else None

    def list(self, *, limit: int = 50, offset: int = 0) -> list[JobRow]:
        with self._Session() as session:
            rows = (
                session.execute(
                    select(Job)
                    .order_by(Job.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
                .scalars()
                .all()
            )
            return [_to_row(job) for job in rows]

    def mark_processing(self, job_id: str) -> None:
        with self._Session() as session:
            job = session.get(Job, job_id)
            if job:
                job.status = JobStatus.processing.value
                session.commit()

    def mark_completed(
        self,
        job_id: str,
        *,
        audio: AudioInfo,
        transcription: Transcription,
        diarization: Diarization,
    ) -> None:
        payload = {
            "audio": audio.model_dump(),
            "transcription": transcription.model_dump(),
            "diarization": diarization.model_dump(),
        }
        with self._Session() as session:
            job = session.get(Job, job_id)
            if job:
                job.status = JobStatus.completed.value
                job.completed_at = _now_iso()
                job.result_json = json.dumps(payload, ensure_ascii=False)
                session.commit()

    def mark_failed(self, job_id: str, error: str) -> None:
        with self._Session() as session:
            job = session.get(Job, job_id)
            if job:
                job.status = JobStatus.failed.value
                job.completed_at = _now_iso()
                job.error = error
                session.commit()

    def delete(self, job_id: str) -> bool:
        """ジョブと音声ファイルを削除する。存在しなければ False。"""
        with self._Session() as session:
            job = session.get(Job, job_id)
            if job is None:
                return False
            audio_path = job.audio_path
            session.delete(job)
            session.commit()
        _unlink(audio_path)
        return True

    def to_result(self, row: JobRow) -> JobResult:
        """JobRow を API 応答用の JobResult に変換する。"""
        data = json.loads(row.result_json) if row.result_json else {}
        audio: Optional[AudioInfo] = None
        if data.get("audio"):
            audio = AudioInfo(**data["audio"])
        elif row.audio_filename:
            audio = AudioInfo(
                filename=row.audio_filename,
                content_type=row.audio_content_type,
            )
        return JobResult(
            job_id=row.id,
            status=row.status,
            audio=audio,
            transcription=(
                Transcription(**data["transcription"])
                if data.get("transcription")
                else None
            ),
            diarization=(
                Diarization(**data["diarization"])
                if data.get("diarization")
                else None
            ),
            error=row.error,
            created_at=row.created_at,
            completed_at=row.completed_at,
        )

    def cleanup_expired(
        self, *, retention_hours: int, now: Optional[datetime] = None
    ) -> int:
        """保持期限を超えたジョブと成果物を削除し、削除件数を返す。"""
        now = now or datetime.now().astimezone()
        cutoff = now - timedelta(hours=retention_hours)
        removed = 0
        with self._Session() as session:
            rows = session.execute(select(Job)).scalars().all()
            for job in rows:
                try:
                    created = datetime.fromisoformat(job.created_at)
                except ValueError:
                    continue
                if created < cutoff:
                    _unlink(job.audio_path)
                    session.delete(job)
                    removed += 1
            session.commit()
        return removed


def _unlink(path: Optional[str]) -> None:
    if not path:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass


# 型エイリアス: (audio_path, *, model, language) -> Transcription
TranscribeFn = Callable[..., Transcription]
# 型エイリアス: (audio_path, *, num_speakers) -> Diarization
DiarizeFn = Callable[..., Diarization]


class WorkerPool:
    """ジョブを逐次処理するバックグラウンドワーカ。

    GPU(Metal) 共有のため concurrency は既定 1。concurrency=0 の場合は
    スレッドを起動せず、`process()` を明示的に呼ぶ手動モードになる
    （テスト用途）。
    """

    def __init__(
        self,
        store: JobStore,
        *,
        transcribe_fn: TranscribeFn,
        diarize_fn: DiarizeFn,
        concurrency: int = 1,
    ) -> None:
        self.store = store
        self.transcribe_fn = transcribe_fn
        self.diarize_fn = diarize_fn
        self.concurrency = concurrency
        self._queue: "queue.Queue[Optional[str]]" = queue.Queue()
        self._threads: list[threading.Thread] = []
        self._stop_sentinel: Optional[str] = None

    def start(self) -> None:
        for _ in range(self.concurrency):
            thread = threading.Thread(target=self._loop, daemon=True)
            thread.start()
            self._threads.append(thread)

    def submit(self, job_id: str) -> None:
        self._queue.put(job_id)

    def _loop(self) -> None:
        while True:
            job_id = self._queue.get()
            try:
                if job_id is self._stop_sentinel:
                    break
                self.process(job_id)
            finally:
                self._queue.task_done()

    def process(self, job_id: str) -> None:
        """1ジョブを文字起こし→話者分離まで実行する。"""
        row = self.store.get(job_id)
        if row is None:
            return
        self.store.mark_processing(job_id)
        try:
            transcription = self.transcribe_fn(
                row.audio_path, model=row.model, language=row.language
            )
            diarization = self.diarize_fn(
                row.audio_path, num_speakers=row.num_speakers
            )
            ends = [s.end for s in transcription.segments] + [
                s.end for s in diarization.segments
            ]
            duration = max(ends) if ends else None
            audio = AudioInfo(
                filename=row.audio_filename,
                content_type=row.audio_content_type,
                duration_sec=duration,
            )
            self.store.mark_completed(
                job_id,
                audio=audio,
                transcription=transcription,
                diarization=diarization,
            )
        except Exception as exc:  # noqa: BLE001 - 失敗はジョブに記録して継続
            self.store.mark_failed(job_id, str(exc))

    def stop(self) -> None:
        for _ in self._threads:
            self._queue.put(self._stop_sentinel)
        for thread in self._threads:
            thread.join(timeout=5)
        self._threads.clear()
