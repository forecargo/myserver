import hashlib
import hmac
import json
import os
from base64 import b64decode, b64encode
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select

from database import get_session
from models import Incident

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_NOTIFICATION_TARGETS = [
    t.strip() for t in os.getenv("LINE_NOTIFICATION_TARGETS", "").split(",") if t.strip()
]
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")
JST = timezone(timedelta(hours=9))

STATUS_COLORS = {
    "発生中": "#EF4444",
    "調査中": "#F59E0B",
    "復旧済み": "#22C55E",
}

HELP_TEXT = """📋 障害インシデント管理

【コマンド一覧】
一覧　　→ 最新インシデント10件
発生中　→ 未解決インシデント
#123　→ インシデント#123の詳細
同期　　→ メール同期を実行
ヘルプ　→ このメッセージ"""

_LINE_API = "https://api.line.me/v2/bot/message"


def verify_signature(body: bytes, sig: str) -> bool:
    if not LINE_CHANNEL_SECRET:
        return True
    digest = hmac.new(LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    expected = b64encode(digest).decode()
    return hmac.compare_digest(expected, sig)


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}", "Content-Type": "application/json"}


def reply_messages(reply_token: str, messages: list) -> None:
    payload = {"replyToken": reply_token, "messages": messages}
    httpx.post(f"{_LINE_API}/reply", headers=_auth_headers(), json=payload, timeout=10)


def push_messages(to: str, messages: list) -> None:
    payload = {"to": to, "messages": messages}
    httpx.post(f"{_LINE_API}/push", headers=_auth_headers(), json=payload, timeout=10)


def text_msg(text: str) -> dict:
    return {"type": "text", "text": text}


def flex_msg(alt_text: str, contents: dict) -> dict:
    return {"type": "flex", "altText": alt_text, "contents": contents}


def _fmt_dt(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.astimezone(JST).strftime("%m/%d %H:%M")


def make_incident_bubble(inc: Incident) -> dict:
    color = STATUS_COLORS.get(inc.status, "#6B7280")
    detail_url = f"{BASE_URL}/?id={inc.id}" if BASE_URL else None

    body_contents = [
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": inc.system_name, "weight": "bold", "size": "md", "wrap": True},
                {
                    "type": "text",
                    "text": inc.failure_type or "障害種別不明",
                    "size": "xs",
                    "color": "#6B7280",
                    "wrap": True,
                    "margin": "xs",
                },
            ],
        },
        {"type": "separator", "margin": "md"},
        {
            "type": "box",
            "layout": "vertical",
            "margin": "md",
            "spacing": "xs",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "発生", "size": "xs", "color": "#6B7280", "flex": 2},
                        {"type": "text", "text": _fmt_dt(inc.occurred_at), "size": "xs", "flex": 5},
                    ],
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "クローズ", "size": "xs", "color": "#6B7280", "flex": 2},
                        {"type": "text", "text": _fmt_dt(inc.closed_at), "size": "xs", "flex": 5},
                    ],
                },
            ],
        },
    ]

    footer_contents = []
    if detail_url:
        footer_contents.append({
            "type": "button",
            "style": "link",
            "height": "sm",
            "action": {"type": "uri", "label": f"詳細 #{inc.id} →", "uri": detail_url},
        })

    bubble: dict = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": color,
            "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": inc.status, "color": "#FFFFFF", "weight": "bold", "size": "sm"}
            ],
        },
        "body": {"type": "box", "layout": "vertical", "contents": body_contents},
    }
    if footer_contents:
        bubble["footer"] = {"type": "box", "layout": "vertical", "contents": footer_contents}

    return bubble


def _incidents_to_flex(incidents: list[Incident], alt_text: str) -> list[dict]:
    if not incidents:
        return [text_msg("該当するインシデントはありません。")]
    bubbles = [make_incident_bubble(inc) for inc in incidents[:12]]
    if len(bubbles) == 1:
        return [flex_msg(alt_text, bubbles[0])]
    return [flex_msg(alt_text, {"type": "carousel", "contents": bubbles})]


def handle_text_event(text: str, reply_token: str) -> None:
    text = text.strip()

    if text in ("ヘルプ", "help", "?", "？"):
        reply_messages(reply_token, [text_msg(HELP_TEXT)])
        return

    if text in ("同期", "sync"):
        from collector import collect_and_process
        result = collect_and_process()
        msg = (
            f"同期完了\n"
            f"新規: {result['new_incidents']}件\n"
            f"更新: {result['updated_incidents']}件\n"
            f"スキップ: {result['skipped']}件"
        )
        if result["errors"]:
            msg += f"\nエラー: {len(result['errors'])}件"
        reply_messages(reply_token, [text_msg(msg)])
        return

    if text in ("発生中", "障害", "未解決"):
        with get_session() as session:
            stmt = (
                select(Incident)
                .where(Incident.status.in_(["発生中", "調査中"]))
                .order_by(Incident.email_received_at.desc())
                .limit(12)
            )
            incidents = session.execute(stmt).scalars().all()
            messages = _incidents_to_flex(incidents, "未解決インシデント一覧")
        reply_messages(reply_token, messages)
        return

    if text in ("一覧", "リスト", "list"):
        with get_session() as session:
            stmt = select(Incident).order_by(Incident.email_received_at.desc()).limit(10)
            incidents = session.execute(stmt).scalars().all()
            messages = _incidents_to_flex(incidents, "最新インシデント一覧")
        reply_messages(reply_token, messages)
        return

    if text.startswith("#"):
        try:
            incident_id = int(text[1:])
        except ValueError:
            reply_messages(reply_token, [text_msg(HELP_TEXT)])
            return
        with get_session() as session:
            inc = session.get(Incident, incident_id)
        if not inc:
            reply_messages(reply_token, [text_msg(f"インシデント #{incident_id} は見つかりませんでした。")])
            return
        detail = (
            f"#{inc.id} {inc.system_name}\n"
            f"種別: {inc.failure_type or '不明'}\n"
            f"状態: {inc.status}\n"
            f"発生: {_fmt_dt(inc.occurred_at)}\n"
            f"クローズ: {_fmt_dt(inc.closed_at)}\n"
            f"概要: {(inc.description or '')[:200]}"
        )
        messages = [flex_msg(f"#{inc.id} {inc.system_name}", make_incident_bubble(inc)), text_msg(detail)]
        reply_messages(reply_token, messages)
        return

    reply_messages(reply_token, [text_msg(HELP_TEXT)])


def notify_new_incidents(ids: list[int]) -> None:
    if not ids or not LINE_NOTIFICATION_TARGETS:
        return
    with get_session() as session:
        incidents = [session.get(Incident, i) for i in ids]
        incidents = [inc for inc in incidents if inc is not None]
    if not incidents:
        return
    messages = _incidents_to_flex(incidents, f"新規障害 {len(incidents)}件")
    for target in LINE_NOTIFICATION_TARGETS:
        push_messages(target, messages)
