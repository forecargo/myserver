"""FastAPI アプリ本体。

起動時に `assets/data/` を読み込んでメモリストアを構築し、単語・慣用句・検索・クイズ・
メタ情報を配信する。暗記カード画像は `/assets` に静的マウントする。
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config
from .models import HealthResponse
from .routers import idioms, meta, quiz, search, words
from .store import Store

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時にデータをロードしてストアを app.state に保持する。"""
    app.state.store = Store.load()
    yield


app = FastAPI(
    title="Kobun API",
    version="0.1.0",
    description="古文単語アプリ「ことだま」向けコンテンツ配信 API（読み取り専用）",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta.router)
app.include_router(words.router)
app.include_router(idioms.router)
app.include_router(search.router)
app.include_router(quiz.router)

# 暗記カード画像（assets/manga/...）を静的配信。
if config.ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(config.ASSETS_DIR)), name="assets")


@app.get("/healthz", response_model=HealthResponse, tags=["health"])
def healthz(request: Request) -> HealthResponse:
    """ヘルスチェック（ロード済み件数を返す）。"""
    store: Store = request.app.state.store
    return HealthResponse(status="ok", words=len(store.words), idioms=len(store.idioms))
