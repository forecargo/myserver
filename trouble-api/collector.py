import email
import os
import ssl
from datetime import datetime, timedelta, timezone
from email.header import decode_header

import imapclient
from dateutil import parser as dtparser
from sqlalchemy import select

from analyzer import analyze_email
from database import get_session
from models import Incident, ProcessedEmail

JST = timezone(timedelta(hours=9))

IMAP_HOST = os.getenv("IMAP_HOST", "imap.spmode.ne.jp")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USERNAME = os.getenv("IMAP_USERNAME")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")
SENDER_FILTER = os.getenv("SENDER_FILTER", "ncbonline@nttdata-ncb.co.jp")
INCIDENT_MATCH_WINDOW_HOURS = int(os.getenv("INCIDENT_MATCH_WINDOW_HOURS", "72"))

RECOVERY_KEYWORDS = (
    "解消", "復旧確認", "正常稼働確認", "正常稼働を確認",
    "業務影響なし", "終了確認", "回復確認", "回復済", "復旧済",
)


def _make_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    # Some older IMAP servers require legacy TLS renegotiation (disabled by default in OpenSSL 3.x)
    ctx.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0x4)
    return ctx


def _decode_str(raw) -> str:
    if isinstance(raw, bytes):
        parts = decode_header(raw.decode("utf-8", errors="replace"))
    else:
        parts = decode_header(str(raw))
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(str(part))
    return "".join(decoded)


def _extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                charset = part.get_content_charset() or "iso-2022-jp"
                return part.get_payload(decode=True).decode(charset, errors="replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="replace")
    else:
        charset = msg.get_content_charset() or "iso-2022-jp"
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(charset, errors="replace")
    return ""


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return dtparser.parse(s)
    except Exception:
        return None


def _find_existing_incident(session, system_name: str, occurred_at_str: str | None) -> Incident | None:
    stmt = (
        select(Incident)
        .where(Incident.system_name == system_name)
        .where(Incident.status == "発生中")
        .order_by(Incident.created_at.desc())
    )
    candidates = session.execute(stmt).scalars().all()
    if not candidates:
        return None
    if occurred_at_str:
        target_dt = _parse_dt(occurred_at_str)
        if target_dt:
            window = timedelta(hours=INCIDENT_MATCH_WINDOW_HOURS)
            for c in candidates:
                if c.occurred_at:
                    diff = abs(
                        c.occurred_at.replace(tzinfo=None) - target_dt.replace(tzinfo=None)
                    )
                    if diff <= window:
                        return c
            return None
    return candidates[0]


def _has_inline_recovery(extracted: dict, body: str) -> bool:
    """単一メール内で解消・復旧確認が事実として記載されているか。

    closed_at が抽出されており、かつ本文または response に
    復旧キーワードが含まれる場合のみ True を返す。
    """
    if not extracted.get("closed_at"):
        return False
    haystack = (body or "") + " " + (extracted.get("response") or "")
    return any(kw in haystack for kw in RECOVERY_KEYWORDS)


def _sanitize_new_incident_status(extracted: dict, body: str = "") -> str:
    status = extracted.get("status", "発生中")
    report_type = extracted.get("report_type", "不明")
    if status != "復旧済み":
        return status
    if report_type in ("最終報", "発生回復報"):
        return "復旧済み"
    if _has_inline_recovery(extracted, body):
        return "復旧済み"
    return "発生中"


def _apply_update(incident: Incident, extracted: dict, received_at: datetime, body: str = "") -> bool:
    """Returns True if status changed."""
    new_status = extracted.get("status")
    report_type = extracted.get("report_type", "不明")
    status_changed = False

    if new_status == "復旧済み" and report_type == "続報" and not _has_inline_recovery(extracted, body):
        new_status = "発生中"

    if extracted.get("closed_at") and incident.closed_at is None and _has_inline_recovery(extracted, body):
        new_status = "復旧済み"

    if new_status:
        if new_status != incident.status:
            status_changed = True
        incident.status = new_status
    if extracted.get("closed_at"):
        incident.closed_at = _parse_dt(extracted["closed_at"])
    if extracted.get("response"):
        ts = received_at.astimezone(JST).strftime("%Y-%m-%d %H:%M") if hasattr(received_at, "astimezone") else str(received_at)
        incident.response = (incident.response or "") + f"\n\n[{ts} 追記]\n{extracted['response']}"
    if extracted.get("description") and not incident.description:
        incident.description = extracted["description"]
    return status_changed


def _filter_uids_by_sender(server, all_uids: list, sender_addr: str) -> list:
    """
    Server-side FROM search is unreliable on some IMAP servers (e.g. iCloud).
    Fetch lightweight headers for all messages and filter by From address in Python.
    Process in batches to avoid oversized requests.
    """
    matching = []
    needle = sender_addr.lower()
    batch_size = 50
    for i in range(0, len(all_uids), batch_size):
        batch = all_uids[i : i + batch_size]
        headers = server.fetch(batch, ["BODY[HEADER.FIELDS (FROM MESSAGE-ID)]", "INTERNALDATE"])
        for uid, data in headers.items():
            raw_hdr = data.get(b"BODY[HEADER.FIELDS (FROM MESSAGE-ID)]", b"")
            from_line = ""
            for line in raw_hdr.decode("utf-8", errors="replace").splitlines():
                if line.lower().startswith("from:"):
                    from_line = line.lower()
                    break
            if needle in from_line:
                matching.append(uid)
    return matching


def collect_and_process(forward_enabled: bool = True) -> dict:
    results = {
        "new_incidents": 0,
        "updated_incidents": 0,
        "skipped": 0,
        "errors": [],
        "new_incident_ids": [],
        "resolved_new_incident_ids": [],
        "status_changed_incident_ids": [],
        "forwarded": 0,
        "forward_skipped": 0,
        "forward_errors": [],
    }

    try:
        with imapclient.IMAPClient(IMAP_HOST, port=IMAP_PORT, ssl=True, ssl_context=_make_ssl_context()) as server:
            server.login(IMAP_USERNAME, IMAP_PASSWORD)
            server.select_folder("INBOX", readonly=False)
            all_uids = server.search(["UNSEEN"])
            uids = _filter_uids_by_sender(server, all_uids, SENDER_FILTER) if all_uids else []
            # BODY.PEEK[] を使う: RFC822 を直接 fetch すると docomo spmode サーバ側で
            # 暗黙的に \Seen が付与され、後続の set_flags が「変化なし」として無視され、
            # セッション終了時に暗黙 \Seen が巻き戻る (= 永続化されない) ため。
            messages = server.fetch(uids, ["BODY.PEEK[]", "INTERNALDATE"]) if uids else {}

            for uid, data in messages.items():
                try:
                    raw_email = data[b"BODY[]"]
                    received_at = data[b"INTERNALDATE"]
                    msg = email.message_from_bytes(raw_email)
                    message_id = msg.get("Message-ID", f"no-id-{uid}").strip()

                    with get_session() as session:
                        if session.get(ProcessedEmail, message_id):
                            results["skipped"] += 1
                            try:
                                server.set_flags([uid], [b"\\Seen"])
                            except Exception as flag_err:
                                results["errors"].append(f"UID {uid}: set_flags failed: {flag_err}")
                            continue

                        subject = _decode_str(msg.get("Subject", ""))
                        body = _extract_body(msg)
                        received_str = (
                            received_at.astimezone(JST).isoformat()
                            if hasattr(received_at, "astimezone")
                            else str(received_at)
                        )

                        extracted = analyze_email(subject, body, received_str)

                        incident = None
                        if extracted.get("is_update"):
                            incident = _find_existing_incident(
                                session,
                                extracted.get("system_name", ""),
                                extracted.get("occurred_at"),
                            )

                        if incident:
                            status_changed = _apply_update(incident, extracted, received_at, body)
                            results["updated_incidents"] += 1
                            if status_changed:
                                results["status_changed_incident_ids"].append(incident.id)
                        else:
                            safe_status = _sanitize_new_incident_status(extracted, body)
                            incident = Incident(
                                system_name=extracted.get("system_name", "不明"),
                                failure_type=extracted.get("failure_type"),
                                status=safe_status,
                                occurred_at=_parse_dt(extracted.get("occurred_at")),
                                closed_at=_parse_dt(extracted.get("closed_at")),
                                description=extracted.get("description"),
                                response=extracted.get("response"),
                                email_subject=subject,
                                email_received_at=received_at,
                                email_message_id=message_id,
                                raw_email_body=body,
                            )
                            session.add(incident)
                            session.flush()
                            results["new_incidents"] += 1
                            if safe_status == "復旧済み":
                                results["resolved_new_incident_ids"].append(incident.id)
                            else:
                                results["new_incident_ids"].append(incident.id)

                        pe = ProcessedEmail(message_id=message_id, incident_id=incident.id)
                        session.add(pe)
                        session.commit()

                    try:
                        server.set_flags([uid], [b"\\Seen"])
                    except Exception as flag_err:
                        results["errors"].append(f"UID {uid}: set_flags failed: {flag_err}")

                except Exception as e:
                    results["errors"].append(f"UID {uid}: {e}")

            if forward_enabled:
                try:
                    from forward_handler import forward_admin_emails
                    forward_admin_emails(server, results)
                except Exception as e:
                    results["forward_errors"].append(f"forward_admin_emails error: {e}")

    except Exception as e:
        results["errors"].append(f"IMAP connection error: {e}")
        return results

    return results
