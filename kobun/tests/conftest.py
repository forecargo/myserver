"""pytest 共通フィクスチャ。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """lifespan を起動してストアをロードした TestClient。"""
    with TestClient(app) as c:
        yield c
