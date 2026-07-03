"""Transcribe API — 音声文字起こし(mlx-whisper) + 話者分離(pyannote.audio)。

非同期ジョブ方式: POST /jobs で受付 → job_id を返却 → GET /jobs/{id} でポーリング。
"""

import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import diarizer
import transcriber
from config import load_settings, validate_settings
from jobs import JobStore, WorkerPool
from models import HealthResponse, JobAccepted, JobResult, JobStatus

logger = logging.getLogger("transcribe-api")

# 許可する content-type と対応拡張子
ALLOWED_TYPES: dict[str, set[str]] = {
    "audio/wav": {".wav"},
    "audio/x-wav": {".wav"},
    "audio/mpeg": {".mp3"},
    "audio/mp4": {".mp4", ".m4a"},
    "audio/m4a": {".m4a"},
    "audio/x-m4a": {".m4a"},
    "audio/flac": {".flac"},
    "audio/x-flac": {".flac"},
    "audio/ogg": {".ogg"},
}
CHUNK_SIZE = 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時にモデル・ワーカを初期化し、終了時にワーカを停止する。"""
    settings = load_settings()
    validate_settings(settings)  # HF_TOKEN 未設定なら fail-fast

    uploads = Path(settings.work_dir) / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)

    store = JobStore(settings.database_url, settings.work_dir)
    pipeline = diarizer.load_pipeline(
        settings.diarization_model, settings.hf_token, settings.pyannote_device
    )

    def _transcribe(audio_path, *, model, language):
        return transcriber.run_transcription(
            audio_path, model=model, language=language
        )

    def _diarize(audio_path, *, num_speakers):
        return diarizer.run_diarization(
            pipeline,
            audio_path,
            model=settings.diarization_model,
            num_speakers=num_speakers,
        )

    worker = WorkerPool(
        store,
        transcribe_fn=_transcribe,
        diarize_fn=_diarize,
        concurrency=settings.worker_concurrency,
    )
    worker.start()

    app.state.settings = settings
    app.state.store = store
    app.state.worker = worker
    app.state.uploads = uploads
    app.state.models_loaded = True
    logger.info(
        "transcribe-api started (model=%s, workers=%d)",
        settings.whisper_model,
        settings.worker_concurrency,
    )
    try:
        yield
    finally:
        worker.stop()


app = FastAPI(title="Transcribe API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validate_upload(file: UploadFile) -> str:
    """content-type と拡張子を検証し、拡張子を返す。"""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"未対応の content-type です: {file.content_type}",
        )
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_TYPES[file.content_type]:
        raise HTTPException(
            status_code=400,
            detail=f"拡張子が content-type と一致しません: {ext or '(なし)'}",
        )
    return ext


@app.post("/jobs", status_code=202, response_model=JobAccepted)
async def create_job(
    file: UploadFile = File(...),
    language: str | None = Form(None),
    model: str | None = Form(None),
    num_speakers: int | None = Form(None),
) -> JobAccepted:
    """音声をアップロードしてジョブを受け付ける。"""
    settings = app.state.settings
    ext = _validate_upload(file)

    job_id = uuid.uuid4().hex
    dest = app.state.uploads / f"{job_id}{ext}"
    max_bytes = settings.max_upload_mb * 1024 * 1024
    size = 0
    try:
        with open(dest, "wb") as out:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"ファイルサイズが上限({settings.max_upload_mb}MB)"
                            "を超えています"
                        ),
                    )
                out.write(chunk)
    except HTTPException:
        dest.unlink(missing_ok=True)
        raise

    row = app.state.store.create(
        job_id=job_id,
        audio_filename=file.filename or f"{job_id}{ext}",
        content_type=file.content_type,
        audio_path=str(dest),
        language=language or settings.whisper_language,
        model=model or settings.whisper_model,
        num_speakers=num_speakers,
    )
    app.state.worker.submit(job_id)
    return JobAccepted(
        job_id=row.id, status=JobStatus(row.status), created_at=row.created_at
    )


@app.get("/jobs", response_model=list[JobResult])
async def list_jobs(limit: int = 50, offset: int = 0) -> list[JobResult]:
    """ジョブ一覧を取得する。"""
    rows = app.state.store.list(limit=limit, offset=offset)
    return [app.state.store.to_result(row) for row in rows]


@app.get("/jobs/{job_id}", response_model=JobResult)
async def get_job(job_id: str) -> JobResult:
    """ジョブの状態と結果を取得する。"""
    row = app.state.store.get(job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="指定されたジョブが見つかりません")
    return app.state.store.to_result(row)


@app.get("/jobs/{job_id}/result", response_model=JobResult)
async def get_job_result(job_id: str) -> JobResult:
    """完了済みジョブの結果を取得する（未完了なら 409）。"""
    row = app.state.store.get(job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="指定されたジョブが見つかりません")
    if row.status != JobStatus.completed.value:
        raise HTTPException(
            status_code=409,
            detail=f"ジョブはまだ完了していません (status={row.status})",
        )
    return app.state.store.to_result(row)


@app.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str) -> None:
    """ジョブと成果物を削除する。"""
    if not app.state.store.delete(job_id):
        raise HTTPException(status_code=404, detail="指定されたジョブが見つかりません")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """ヘルスチェック。"""
    return HealthResponse(
        status="ok", models_loaded=getattr(app.state, "models_loaded", False)
    )
