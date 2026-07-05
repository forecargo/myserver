"""FastAPI 依存性。"""

from __future__ import annotations

from fastapi import Request

from .store import Store


def get_store(request: Request) -> Store:
    """lifespan で構築済みのストアを返す。"""
    return request.app.state.store
