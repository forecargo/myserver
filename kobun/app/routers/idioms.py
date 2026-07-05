"""慣用句エンドポイント。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_store
from ..models import IdiomDetail, IdiomListItem, IdiomListResponse
from ..store import Store

router = APIRouter(prefix="/api", tags=["idioms"])


@router.get("/idioms", response_model=IdiomListResponse, response_model_exclude_none=True)
def list_idioms(
    q: str | None = Query(None, description="見出し・読み・語義の部分一致検索"),
    ids: str | None = Query(None, description="idiom_id のカンマ区切り一括取得（指定順を保持）"),
    limit: int | None = Query(None, ge=1, le=500),
    offset: int = Query(0, ge=0),
    store: Store = Depends(get_store),
) -> IdiomListResponse:
    """条件に合致する慣用句の一覧を返す。``ids`` 指定時はページングせず指定順で返す。"""
    id_list = [s.strip() for s in ids.split(",") if s.strip()] if ids is not None else None
    items: list[IdiomListItem] = store.list_idioms(q=q, ids=id_list)
    total = len(items)
    if id_list is None:
        end = offset + limit if limit is not None else None
        items = items[offset:end]
    return IdiomListResponse(total=total, limit=limit, offset=offset, items=items)


@router.get("/idioms/{idiom_id}", response_model=IdiomDetail, response_model_exclude_none=True)
def get_idiom(idiom_id: str, store: Store = Depends(get_store)) -> IdiomDetail:
    """慣用句詳細を返す。"""
    idiom = store.get_idiom(idiom_id)
    if idiom is None:
        raise HTTPException(status_code=404, detail=f"idiom not found: {idiom_id}")
    return idiom
