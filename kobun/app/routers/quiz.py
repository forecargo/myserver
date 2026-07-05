"""クイズ（4 択）エンドポイント。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..deps import get_store
from ..models import QuizResponse
from ..store import Store

router = APIRouter(prefix="/api", tags=["quiz"])


@router.get("/quiz", response_model=QuizResponse)
def get_quiz(
    section: str | None = Query(None, description="出題範囲の区分（part1 / part2 / keigo）"),
    pos: str | None = Query(None, description="出題範囲の品詞"),
    count: int = Query(10, ge=1, le=50, description="出題数"),
    choices: int = Query(4, ge=2, le=6, description="選択肢数"),
    store: Store = Depends(get_store),
) -> QuizResponse:
    """見出し語の意味を当てる 4 択問題を返す。採点は端末側で行う（answer_index 同梱）。"""
    return store.quiz(section=section, pos=pos, count=count, choices=choices)
