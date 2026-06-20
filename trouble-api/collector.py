import email
import os
import re
import ssl
import unicodedata
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
INCIDENT_MATCH_WINDOW_HOURS = int(os.getenv("INCIDENT_MATCH_WINDOW_HOURS", "672"))

RECOVERY_KEYWORDS = (
    "解消", "復旧確認", "正常稼働確認", "正常稼働を確認",
    "業務影響なし", "終了確認", "回復確認", "回復済", "復旧済",
)

# システム名の正規化用パターン
_PAREN_RE = re.compile(r"[（(][^）)]*[）)]")
_WS_RE = re.compile(r"\s+")


def normalize_system_name(name: str | None) -> str:
    """システム名の表記揺れを吸収するための正規化。

    - NFKC 正規化（全角英数→半角、全角空白→半角等）
    - 全角/半角カッコ内の補足表現を除去
    - 連続空白を単一化してトリム
    - ASCII 部分は小文字化（日本語はそのまま）
    """
    if not name:
        return ""
    s = unicodedata.normalize("NFKC", name)
    s = _PAREN_RE.sub("", s)
    s = _WS_RE.sub(" ", s).strip()
    return "".join(ch.lower() if ch.isascii() else ch for ch in s)


def _strip_tz(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


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


def _find_existing_incident(
    session, system_name: str, occurred_at_str: str | None
) -> Incident | None:
    """発生中インシデントの中から、system_name の表記揺れを吸収して同一とみなせる
    インシデントを返す。Pass1=正規化後完全一致、Pass2=正規化後の双方向 prefix。
    """
    target_norm = normalize_system_name(system_name)
    if not target_norm:
        return None

    stmt = (
        select(Incident)
        .where(Incident.status == "発生中")
        .order_by(Incident.created_at.desc())
    )
    candidates = session.execute(stmt).scalars().all()
    if not candidates:
        return None

    target_dt = _parse_dt(occurred_at_str) if occurred_at_str else None
    window = timedelta(hours=INCIDENT_MATCH_WINDOW_HOURS)

    def _within_window(c: Incident) -> bool:
        if target_dt is None or c.occurred_at is None:
            return True
        diff = abs(_strip_tz(c.occurred_at) - _strip_tz(target_dt))
        return diff <= window

    # Pass 1: 正規化後の完全一致
    exact = [
        c for c in candidates
        if normalize_system_name(c.system_name) == target_norm and _within_window(c)
    ]
    if exact:
        return _pick_closest(exact, target_dt)

    # Pass 2: 正規化後の前方一致（短い側が長い側の prefix、3 文字以上のガード）
    if len(target_norm) >= 3:
        prefix = []
        for c in candidates:
            cn = normalize_system_name(c.system_name)
            if not cn or len(cn) < 3 or not _within_window(c):
                continue
            if cn.startswith(target_norm) or target_norm.startswith(cn):
                prefix.append(c)
        if prefix:
            return _pick_closest(prefix, target_dt)

    return None


def _pick_closest(cands: list[Incident], target_dt: datetime | None) -> Incident:
    """occurred_at が target_dt に最も近い候補を返す。target_dt が None なら
    created_at が最新の候補を返す。"""
    if target_dt is None:
        return max(cands, key=lambda c: c.created_at)

    def _key(c: Incident) -> timedelta:
        if c.occurred_at is None:
            return timedelta.max
        return abs(_strip_tz(c.occurred_at) - _strip_tz(target_dt))

    return min(cands, key=_key)


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
