import json
import os
import re

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_factory, get_session
from models import Diagram, Message
from schemas import ChatRequest

router = APIRouter(tags=["chat"])

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
MAX_HISTORY = 20

_SYSTEM_PROMPT = """\
あなたは Mermaid シーケンス図の編集アシスタントです。

ユーザーの指示に従い、現在の Mermaid コードを修正または新規作成してください。

## 必須ルール
1. 応答には必ず最新の完全な Mermaid コードを含めること
2. Mermaid コードは必ず ```mermaid ～ ``` で囲むこと
3. コードブロック以外に、変更内容の簡単な説明（日本語）を書くこと
4. コードは常に有効な Mermaid 構文であること

## sequenceDiagram の構文ルール

### 参加者の宣言
| 種別 | 記法 | 用途 |
|------|------|------|
| 人・担当者 | `actor 担当者名` | 人間・組織の担当者 |
| システム・装置 | `participant システム名` | IT システム、機器、外部サービス |

- 参加者は図の上部にまとめて宣言する
- エイリアスを使う場合: `actor T as 担当者`

### メッセージの種類
| 矢印 | 意味 |
|------|------|
| `A->>B: メッセージ` | 同期リクエスト（実線矢印） |
| `A-->>B: メッセージ` | レスポンス・戻り値（点線矢印） |
| `A-)B: メッセージ` | 非同期メッセージ |
| `A--xB: メッセージ` | 失敗・エラーの返却 |

- メッセージ名は「動詞＋目的語」の日本語で統一する（例: `申込書を送付する`）

### 制御構造
```
loop 繰り返し条件
    A->>B: ...
end

alt 条件A
    A->>B: ...
else 条件B
    A->>C: ...
end

opt 任意処理
    A->>B: ...
end

par 並行処理A
    A->>B: ...
and 並行処理B
    A->>C: ...
end
```

### 活性化バー（任意）
```
activate A
A->>B: 処理依頼
B-->>A: 完了
deactivate A
```
または省略記法: `A->>+B:` / `B-->>-A:`

### 注釈
```
Note over A,B: 補足テキスト
Note right of A: 補足テキスト
```

### 適用例
```mermaid
sequenceDiagram
    actor 営業担当
    participant 事務センター
    participant 基幹システム

    営業担当->>事務センター: 申込書を送付する
    事務センター->>基幹システム: 申込内容を登録する
    基幹システム-->>事務センター: 登録完了を返す

    alt 不備あり
        事務センター-->>営業担当: 差し戻す
        営業担当->>事務センター: 修正書類を再送する
    else 問題なし
        事務センター-->>営業担当: 受付完了を通知する
    end
```

## 対応する図の種類
- sequenceDiagram（シーケンス図）← メイン
- flowchart（フローチャート）
- classDiagram（クラス図）
- stateDiagram-v2（状態遷移図）
- erDiagram（ER 図）

## 現在の Mermaid コード
{current_mermaid_code}
"""

_MERMAID_RE = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)


@router.post("/diagrams/{diagram_id}/chat")
async def chat_stream(
    diagram_id: int,
    body: ChatRequest,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Diagram).where(Diagram.id == diagram_id))
    diagram = result.scalar_one_or_none()
    if not diagram:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    hist_result = await session.execute(
        select(Message)
        .where(Message.diagram_id == diagram_id)
        .order_by(Message.created_at.desc())
        .limit(MAX_HISTORY)
    )
    history = list(reversed(hist_result.scalars().all()))

    user_msg = Message(diagram_id=diagram_id, role="user", content=body.message)
    session.add(user_msg)
    await session.commit()

    anthropic_messages = [{"role": m.role, "content": m.content} for m in history]
    anthropic_messages.append({"role": "user", "content": body.message})
    system = _SYSTEM_PROMPT.format(current_mermaid_code=diagram.mermaid_code)

    async def event_generator():
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        full_response = ""

        try:
            async with client.messages.stream(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=system,
                messages=anthropic_messages,
            ) as stream:
                async for text in stream.text_stream:
                    full_response += text
                    yield f"event: token\ndata: {json.dumps({'type': 'token', 'content': text})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        match = _MERMAID_RE.search(full_response)
        if match:
            mermaid_code = match.group(1).strip()
            async with async_session_factory() as update_session:
                diag = await update_session.get(Diagram, diagram_id)
                if diag:
                    diag.mermaid_code = mermaid_code
                    await update_session.commit()
            yield f"event: mermaid\ndata: {json.dumps({'type': 'mermaid', 'code': mermaid_code})}\n\n"

        async with async_session_factory() as update_session:
            ai_msg = Message(diagram_id=diagram_id, role="assistant", content=full_response)
            update_session.add(ai_msg)
            await update_session.commit()

        yield f"event: done\ndata: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
