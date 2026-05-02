from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from google import genai
from google.genai import types
import io
import os
import json
import re
import base64

app = FastAPI(title="Schedule API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise RuntimeError("GEMINI_API_KEY が設定されていません")
client = genai.Client(api_key=gemini_api_key)

SCHEDULE_PROMPT = """与えられた画像からスケジュール予約を読み取り、以下のフォーマットでJSONをコードブロックとして出力してください。

## フォーマット

```json
[
    {
        "date": "YYYY/MM/DD",
        "day_of_week": "月〜日のいずれか",
        "start_time": "HH:MM",
        "end_time": "HH:MM",
        "category": "会議 など",
        "title": "予定のタイトル",
        "location": "場所",
        "reserver": "予約者名"
    }
]
```

- 読み取れない項目は空文字列にしてください。
- 複数の予定がある場合はすべて配列に含めてください。
- JSONコードブロック以外の説明文は不要です。"""

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/index.html")

@app.get("/support", include_in_schema=False)
def support():
    return RedirectResponse(url="/static/support.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/schedule")
async def schedule(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="jpeg/png/webp のみ対応")

    contents = await file.read()

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=[
                types.Part.from_text(text=SCHEDULE_PROMPT),
                types.Part.from_bytes(data=contents, mime_type=file.content_type),
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini API エラー: {e}")

    raw = response.text
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if not match:
        raise HTTPException(status_code=500, detail=f"JSONブロックが見つかりませんでした: {raw}")

    try:
        schedules = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSONパースエラー: {e}")

    return {"schedules": schedules}
