import json
import os
import re

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3.1-flash-lite-preview"

ANALYSIS_PROMPT = """以下はシステム障害通知メールです。内容を解析し、JSON形式で情報を抽出してください。

## 抽出ルール
- system_name: 障害が発生したシステム名。不明な場合は件名から推測してください。
- failure_type: 障害の種別（例: ログイン障害、接続障害、処理遅延、サービス停止など）
- status: メール内容から以下のいずれかを判定してください:
  - "発生中": 障害が発生し、まだ解決していない
  - "調査中": 原因調査中または対応中
  - "復旧済み": サービスが復旧・解決済み（根本原因調査中・完全クローズ問わず）
- occurred_at: 障害発生日時 (ISO 8601形式: "YYYY-MM-DDTHH:MM:SS+09:00")。不明な場合はnull
- closed_at: 復旧・解決日時 (ISO 8601形式)。未復旧の場合はnull
- description: 障害の内容説明（日本語、200字以内）
- response: 対応内容・対処状況（日本語、200字以内）
- is_update: このメールが既存障害の続報・更新・解消通知かどうか (true/false)
- update_hint: is_updateがtrueの場合、関連する既存障害のsystem_nameとoccurred_atのヒント

## メール件名
{subject}

## メール受信日時（参考）
{received_at}

## メール本文
{body}

## 出力形式
必ずJSONコードブロックのみを出力してください。説明文は不要です。

```json
{{
  "system_name": "システム名",
  "failure_type": "障害種別",
  "status": "発生中",
  "occurred_at": "2025-01-01T09:00:00+09:00",
  "closed_at": null,
  "description": "障害の詳細説明",
  "response": "対応内容",
  "is_update": false,
  "update_hint": null
}}
```"""


def analyze_email(subject: str, body: str, received_at: str) -> dict:
    prompt = ANALYSIS_PROMPT.format(
        subject=subject,
        body=body[:3000],
        received_at=received_at,
    )
    response = client.models.generate_content(
        model=MODEL,
        contents=[types.Part.from_text(text=prompt)],
    )
    raw = response.text
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if match:
        return json.loads(match.group(1))
    return json.loads(raw.strip())
