"""メタ情報エンドポイント。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import get_store
from ..models import MetaResponse
from ..store import Store

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/meta", response_model=MetaResponse)
def get_meta(store: Store = Depends(get_store)) -> MetaResponse:
    """区分・件数・品詞内訳を返す（単語帳の章ヘッダ・品詞タブ用）。"""
    return store.meta()
