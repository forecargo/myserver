import hashlib
import hmac
import os
import re
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select

from database import get_session
from models import Incident

WEBEX_BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN", "")
WEBEX_WEBHOOK_SECRET = os.getenv("WEBEX_WEBHOOK_SECRET", "")
WEBEX_BOT_EMAIL = os.getenv("WEBEX_BOT_EMAIL", "").lower()
WEBEX_BOT_NAME = os.getenv("WEBEX_BOT_NAME", "")
WEBEX_NOTIFICATION_TARGETS = [
    t.strip() for t in os.getenv("WEBEX_NOTIFICATION_TARGETS", "").split(",") if t.strip()
]

JST = timezone(timedelta(hours=9))
_WEBEX_API = "https://webexapis.com/v1"

STATUS_EMOJI = {
    "発生中": "🔴",
    "復旧済み": "🟢",
}

HELP_TEXT = (
    "## 📋 障害インシデント管理\n\n"
    "| コマンド | 説明 |\n"
    "|---|---|\n"
    "| 一覧 | 最新インシデント10件 |\n"
    "| 発生中 | 未解決インシデント |\n"
    "| #123 | インシデント #123 の詳細 |\n"
    "| 同期 | メール同期を実行 |\n"
    "| ヘルプ | このメッセージ |\n"
)


def verify_signature(body: bytes, sig: str) -> bool:
    if not WEBEX_WEBHOOK_SECRET:
        return True
    digest = hmac.new(WEBEX_WEBHOOK_SECRET.encode(), body, hashlib.sha1).hexdigest()
    return hmac.compare_digest(digest, (sig or "").lower())


def is_allowed_source(payload: dict) -> bool:
    if not WEBEX_NOTIFICATION_TARGETS:
        return True
    room_id = (payload.get("data") or {}).get("roomId")
    return bool(room_id) and room_id in WEBEX_NOTIFICATION_TARGETS


def is_bot_message(payload: dict) -> bool:
    person_email = ((payload.get("data") or {}).get("personEmail") or "").lower()
    return bool(WEBEX_BOT_EMAIL) and person_email == WEBEX_BOT_EMAIL


def _auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {WEBEX_BOT_TOKEN}",
        "Content-Type": "application/json",
    }


def fetch_message_content(message_id: str) -> dict:
    try:
        r = httpx.get(
            f"{_WEBEX_API}/messages/{message_id}",
            headers=_auth_headers(),
            timeout=10,
        )
    except Exception as e:
        print(f"WebEx fetch_message_content error: {e}", flush=True)
        return {}
    if r.status_code != 200:
        print(f"WebEx fetch_message_content failed: {r.status_code} {r.text}", flush=True)
        return {}
    return r.json()


def strip_bot_mention(text: str) -> str:
    # Webex の `text` フィールドはメンションを @ なしの displayName で返すため、
    # 設定済みの Bot 名を優先的に取り除いた上で、念のため "@name " 形式も除去する。
    s = (text or "").lstrip()
    if WEBEX_BOT_NAME and s.startswith(WEBEX_BOT_NAME):
        s = s[len(WEBEX_BOT_NAME):].lstrip()
    s = re.sub(r"^@\S+\s+", "", s)
    return s


def send_message(room_id: str, markdown: str, attachments: list | None = None) -> None:
    payload: dict = {"roomId": room_id, "markdown": markdown}
    if attachments:
        payload["attachments"] = attachments
    try:
        r = httpx.post(
            f"{_WEBEX_API}/messages",
            headers=_auth_headers(),
            json=payload,
            timeout=10,
        )
    except Exception as e:
        print(f"WebEx send_message error: {e}", flush=True)
        return
    if r.status_code >= 400:
        print(f"WebEx send_message failed: {r.status_code} {r.text}", flush=True)


def _fmt_dt(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.astimezone(JST).strftime("%m/%d %H:%M")


_DETAIL_MAX_LEN = 300


def _truncate(text: str | None, limit: int = _DETAIL_MAX_LEN) -> str:
    if not text:
        return "—"
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def make_incident_markdown(inc: Incident, include_details: bool = False) -> str:
    emoji = STATUS_EMOJI.get(inc.status, "⚪")
    lines = [
        f"**{emoji} #{inc.id} {inc.system_name}**",
        f"- 種別: {inc.failure_type or '不明'}",
        f"- 状態: {inc.status}",
        f"- 発生: {_fmt_dt(inc.occurred_at)}",
        f"- クローズ: {_fmt_dt(inc.closed_at)}",
    ]
    if include_details:
        lines.append("")
        lines.append(f"**障害詳細**: {_truncate(inc.description)}")
        lines.append(f"**対応内容**: {_truncate(inc.response)}")
    return "\n".join(lines)


def _incidents_to_markdown(incidents: list[Incident], title: str, include_details: bool = False) -> str:
    if not incidents:
        return "該当するインシデントはありません。"
    body = "\n\n---\n\n".join(
        make_incident_markdown(inc, include_details=include_details) for inc in incidents[:12]
    )
    return f"### {title}\n\n{body}"


def handle_text_event(text: str, room_id: str) -> None:
    text = text.strip()

    if text in ("ヘルプ", "help", "?", "？"):
        send_message(room_id, HELP_TEXT)
        return

    if text in ("同期", "sync"):
        from sync_runner import sync_and_notify
        result = sync_and_notify(send_line=False, send_webex=True)
        msg = (
            "**同期完了**\n"
            f"- 新規: {result['new_incidents']}件\n"
            f"- 更新: {result['updated_incidents']}件\n"
            f"- スキップ: {result['skipped']}件"
        )
        if result["errors"]:
            msg += f"\n- エラー: {len(result['errors'])}件"
        send_message(room_id, msg)
        return

    if text in ("発生中", "障害", "未解決"):
        with get_session() as session:
            stmt = (
                select(Incident)
                .where(Incident.status == "発生中")
                .order_by(Incident.email_received_at.desc())
                .limit(12)
            )
            incidents = session.execute(stmt).scalars().all()
            msg = _incidents_to_markdown(incidents, "未解決インシデント一覧")
        send_message(room_id, msg)
        return

    if text in ("一覧", "リスト", "list"):
        with get_session() as session:
            stmt = select(Incident).order_by(Incident.email_received_at.desc()).limit(10)
            incidents = session.execute(stmt).scalars().all()
            msg = _incidents_to_markdown(incidents, "最新インシデント一覧")
        send_message(room_id, msg)
        return

    if text.startswith("#"):
        try:
            incident_id = int(text[1:])
        except ValueError:
            send_message(room_id, HELP_TEXT)
            return
        with get_session() as session:
            inc = session.get(Incident, incident_id)
        if not inc:
            send_message(room_id, f"インシデント #{incident_id} は見つかりませんでした。")
            return
        detail = make_incident_markdown(inc, include_details=True)
        send_message(room_id, detail)
        return

    send_message(room_id, HELP_TEXT)


def notify_new_incidents(ids: list[int]) -> None:
    if not ids or not WEBEX_NOTIFICATION_TARGETS:
        return
    with get_session() as session:
        incidents = [session.get(Incident, i) for i in ids]
        incidents = [inc for inc in incidents if inc is not None]
    if not incidents:
        return
    msg = _incidents_to_markdown(incidents, f"🔴 新規障害 {len(incidents)}件", include_details=True)
    for room_id in WEBEX_NOTIFICATION_TARGETS:
        send_message(room_id, msg)


def notify_updated_incidents(ids: list[int]) -> None:
    if not ids or not WEBEX_NOTIFICATION_TARGETS:
        return
    with get_session() as session:
        incidents = [session.get(Incident, i) for i in ids]
        incidents = [inc for inc in incidents if inc is not None]
    if not incidents:
        return
    msg = _incidents_to_markdown(incidents, f"🔁 障害ステータス更新 {len(incidents)}件", include_details=True)
    for room_id in WEBEX_NOTIFICATION_TARGETS:
        send_message(room_id, msg)


def notify_resolved_incidents(ids: list[int]) -> None:
    if not ids or not WEBEX_NOTIFICATION_TARGETS:
        return
    with get_session() as session:
        incidents = [session.get(Incident, i) for i in ids]
        incidents = [inc for inc in incidents if inc is not None]
    if not incidents:
        return
    msg = _incidents_to_markdown(incidents, f"🟢 復旧済み障害のお知らせ {len(incidents)}件", include_details=True)
    for room_id in WEBEX_NOTIFICATION_TARGETS:
        send_message(room_id, msg)


def send_sample_notification() -> bool:
    if not WEBEX_NOTIFICATION_TARGETS:
        return False
    from types import SimpleNamespace
    now = datetime.now(JST)
    sample = SimpleNamespace(
        id=0,
        system_name="NCBオンラインバンキング",
        failure_type="ログイン不可",
        status="発生中",
        occurred_at=now,
        closed_at=None,
        description="一部のお客様においてオンラインバンキングへのログインができない障害が発生しております。現在調査中です。",
        response=None,
    )
    msg = _incidents_to_markdown([sample], "新規障害（サンプル通知）", include_details=True)
    for room_id in WEBEX_NOTIFICATION_TARGETS:
        send_message(room_id, msg)
    return True
