import email
import os
import re
from datetime import datetime, timedelta, timezone

import httpx

from database import get_session
from models import ForwardedEmail
from webex_handler import (
    WEBEX_NOTIFICATION_TARGETS,
    _WEBEX_API,
    _auth_headers,
)

JST = timezone(timedelta(hours=9))

FORWARD_ADMIN_SENDER = os.getenv("FORWARD_ADMIN_SENDER", "").strip()
FORWARD_ADMIN_LABEL = os.getenv("FORWARD_ADMIN_LABEL", "e-kakushin").strip()
FORWARD_BODY_EXCERPT_LEN = int(os.getenv("FORWARD_BODY_EXCERPT_LEN", "600"))

# 個人別の報告画面 URL が記載されるため、本文中の URL は公開せずに案内文に置き換える
_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
_FORWARD_GUIDANCE = "🔗 各人に届いたメールのリンクから報告してください"


def _strip_urls(text: str) -> str:
    if not text:
        return ""
    cleaned = _URL_PATTERN.sub("", text)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _fmt_dt(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    if hasattr(dt, "astimezone"):
        return dt.astimezone(JST).strftime("%m/%d %H:%M")
    return str(dt)


def _truncate(text: str | None, limit: int) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def _build_forward_markdown(
    subject: str,
    sender: str,
    received_at: datetime | None,
    body_excerpt: str,
    label: str,
) -> str:
    lines = [
        f"### 📧 [{label}] 管理者宛メール",
        f"- 差出人: {sender or '不明'}",
        f"- 件名: {subject or '(件名なし)'}",
        f"- 受信: {_fmt_dt(received_at)}",
        "",
        "---",
        "",
        body_excerpt or "(本文なし)",
        "",
        "---",
        "",
        _FORWARD_GUIDANCE,
    ]
    return "\n".join(lines)


def _post_to_webex(room_id: str, markdown: str) -> bool:
    try:
        r = httpx.post(
            f"{_WEBEX_API}/messages",
            headers=_auth_headers(),
            json={"roomId": room_id, "markdown": markdown},
            timeout=10,
        )
    except Exception as e:
        print(f"WebEx forward post error (room {room_id}): {e}", flush=True)
        return False
    if r.status_code >= 400:
        print(
            f"WebEx forward post failed (room {room_id}): {r.status_code} {r.text}",
            flush=True,
        )
        return False
    return True


def forward_admin_emails(server, results: dict) -> None:
    """指定送信元 (FORWARD_ADMIN_SENDER) の未読メールを WebEx に転送する。

    server は collector が開いた imapclient セッションを共有する。
    成功したメールは ForwardedEmail に記録し、IMAP 上で既読化する。
    失敗時は未読のまま残し、次回巡回で再試行できるようにする。
    """
    if not FORWARD_ADMIN_SENDER:
        return
    if not WEBEX_NOTIFICATION_TARGETS:
        return

    # collector の循環参照を避けるため遅延 import
    from collector import _decode_str, _extract_body, _filter_uids_by_sender

    try:
        all_uids = server.search(["UNSEEN"])
        if not all_uids:
            return
        uids = _filter_uids_by_sender(server, all_uids, FORWARD_ADMIN_SENDER)
        if not uids:
            return
        messages = server.fetch(uids, ["RFC822", "INTERNALDATE"])
    except Exception as e:
        results["forward_errors"].append(f"forward fetch error: {e}")
        return

    for uid, data in messages.items():
        try:
            raw_email = data[b"RFC822"]
            received_at = data[b"INTERNALDATE"]
            msg = email.message_from_bytes(raw_email)
            message_id = msg.get("Message-ID", f"no-id-{uid}").strip()

            with get_session() as session:
                if session.get(ForwardedEmail, message_id):
                    results["forward_skipped"] += 1
                    try:
                        server.set_flags([uid], [b"\\Seen"])
                    except Exception as flag_err:
                        results["forward_errors"].append(
                            f"UID {uid}: set_flags failed: {flag_err}"
                        )
                    continue

            subject = _decode_str(msg.get("Subject", ""))
            sender = _decode_str(msg.get("From", "")) or FORWARD_ADMIN_SENDER
            body = _extract_body(msg)
            excerpt = _truncate(_strip_urls(body), FORWARD_BODY_EXCERPT_LEN)

            markdown = _build_forward_markdown(
                subject=subject,
                sender=sender,
                received_at=received_at,
                body_excerpt=excerpt,
                label=FORWARD_ADMIN_LABEL,
            )

            sent_any = False
            for room_id in WEBEX_NOTIFICATION_TARGETS:
                if _post_to_webex(room_id, markdown):
                    sent_any = True

            if not sent_any:
                results["forward_errors"].append(
                    f"UID {uid}: WebEx send failed for all rooms"
                )
                continue

            try:
                with get_session() as session:
                    session.add(
                        ForwardedEmail(
                            message_id=message_id,
                            sender=(sender or "")[:200],
                            subject=(subject or "")[:500] or None,
                            email_received_at=received_at if hasattr(received_at, "astimezone") else None,
                        )
                    )
                    session.commit()
            except Exception as db_err:
                results["forward_errors"].append(
                    f"UID {uid}: DB record failed: {db_err}"
                )
                continue

            try:
                server.set_flags([uid], [b"\\Seen"])
            except Exception as flag_err:
                results["forward_errors"].append(
                    f"UID {uid}: set_flags failed: {flag_err}"
                )

            results["forwarded"] += 1

        except Exception as e:
            results["forward_errors"].append(f"UID {uid}: {e}")


def send_test_forward_notification() -> bool:
    """`/webex/test-forward` から呼ばれる疎通テスト用関数。"""
    if not WEBEX_NOTIFICATION_TARGETS:
        return False
    now = datetime.now(JST)
    sample_body = (
        "これは /webex/test-forward から送信されたサンプル転送通知です。\n"
        "本文中の URL（例: https://example.com/report/12345 ）は除去されます。"
    )
    markdown = _build_forward_markdown(
        subject="サンプル: 管理者宛メール転送テスト",
        sender=FORWARD_ADMIN_SENDER or "admin@example.com",
        received_at=now,
        body_excerpt=_truncate(_strip_urls(sample_body), FORWARD_BODY_EXCERPT_LEN),
        label=FORWARD_ADMIN_LABEL,
    )
    ok = False
    for room_id in WEBEX_NOTIFICATION_TARGETS:
        if _post_to_webex(room_id, markdown):
            ok = True
    return ok
