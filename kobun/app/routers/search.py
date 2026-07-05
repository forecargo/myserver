"""横断検索エンドポイント。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..deps import get_store
from ..models import SearchResponse
from ..store import Store

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=SearchResponse, response_model_exclude_none=True)
def search(
    q: str = Query(..., min_length=1, description="検索語（見出し・読み・語義）"),
    limit: int = Query(20, ge=1, le=200, description="単語・慣用句それぞれの最大件数"),
    store: Store = Depends(get_store),
) -> SearchResponse:
    """単語と慣用句を横断して検索する。"""
    words = store.list_words(q=q)[:limit]
    idioms = store.list_idioms(q=q)[:limit]
    return SearchResponse(words=words, idioms=idioms)
