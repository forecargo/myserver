"""単語エンドポイント。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_store
from ..models import WordDetail, WordListItem, WordListResponse
from ..store import Store

router = APIRouter(prefix="/api", tags=["words"])


def _parse_ids(ids: str | None) -> list[str] | None:
    if ids is None:
        return None
    return [s.strip() for s in ids.split(",") if s.strip()]


@router.get("/words", response_model=WordListResponse, response_model_exclude_none=True)
def list_words(
    section: str | None = Query(None, description="part1 / part2 / keigo"),
    pos: str | None = Query(None, description="品詞（動詞・形容詞・形容動詞・名詞・副詞・敬語）"),
    q: str | None = Query(None, description="見出し・読み・語義の部分一致検索"),
    ids: str | None = Query(None, description="entry_no のカンマ区切り一括取得（指定順を保持）"),
    limit: int | None = Query(None, ge=1, le=500),
    offset: int = Query(0, ge=0),
    store: Store = Depends(get_store),
) -> WordListResponse:
    """条件に合致する単語の一覧を返す。``ids`` 指定時はページングせず指定順で返す。"""
    id_list = _parse_ids(ids)
    items: list[WordListItem] = store.list_words(section=section, pos=pos, q=q, ids=id_list)
    total = len(items)
    if id_list is None:
        end = offset + limit if limit is not None else None
        items = items[offset:end]
    return WordListResponse(total=total, limit=limit, offset=offset, items=items)


@router.get("/words/{entry_no}", response_model=WordDetail, response_model_exclude_none=True)
def get_word(entry_no: str, store: Store = Depends(get_store)) -> WordDetail:
    """単語詳細を返す。"""
    word = store.get_word(entry_no)
    if word is None:
        raise HTTPException(status_code=404, detail=f"word not found: {entry_no}")
    return word
