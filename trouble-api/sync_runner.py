from collector import collect_and_process
from line_handler import (
    LINE_NOTIFICATION_TARGETS,
    check_quota as line_check_quota,
    notify_new_incidents,
    notify_resolved_incidents,
    notify_updated_incidents,
)
from webex_handler import (
    WEBEX_NOTIFICATION_TARGETS,
    notify_new_incidents as webex_notify_new_incidents,
    notify_resolved_incidents as webex_notify_resolved_incidents,
    notify_updated_incidents as webex_notify_updated_incidents,
)


def _line_quota_ok() -> bool:
    q = line_check_quota()
    if q is None:
        return True
    remaining = q.get("remaining")
    return remaining is None or remaining > 0


def sync_and_notify(send_line: bool = True, send_webex: bool = True) -> dict:
    """メール収集後、指定プラットフォームにのみ通知をディスパッチする。

    Args:
        send_line: True なら LINE 通知を送る（既定）。Bot コマンド経由でプラットフォーム
            ローカルに留めたい場合は False。
        send_webex: True なら WebEx 通知を送る（既定）。
    """
    result = collect_and_process()
    has_payload = bool(
        result["new_incident_ids"]
        or result.get("resolved_new_incident_ids")
        or result.get("status_changed_incident_ids")
    )
    line_enabled = (
        send_line
        and bool(LINE_NOTIFICATION_TARGETS)
        and (not has_payload or _line_quota_ok())
    )
    webex_enabled = send_webex and bool(WEBEX_NOTIFICATION_TARGETS)
    if result["new_incident_ids"] and line_enabled:
        try:
            notify_new_incidents(result["new_incident_ids"])
        except Exception as e:
            print(f"LINE notify error (new): {e}", flush=True)
    if result.get("resolved_new_incident_ids") and line_enabled:
        try:
            notify_resolved_incidents(result["resolved_new_incident_ids"])
        except Exception as e:
            print(f"LINE notify error (resolved): {e}", flush=True)
    if result.get("status_changed_incident_ids") and line_enabled:
        try:
            notify_updated_incidents(result["status_changed_incident_ids"])
        except Exception as e:
            print(f"LINE notify error (updated): {e}", flush=True)
    if result["new_incident_ids"] and webex_enabled:
        try:
            webex_notify_new_incidents(result["new_incident_ids"])
        except Exception as e:
            print(f"WebEx notify error (new): {e}", flush=True)
    if result.get("resolved_new_incident_ids") and webex_enabled:
        try:
            webex_notify_resolved_incidents(result["resolved_new_incident_ids"])
        except Exception as e:
            print(f"WebEx notify error (resolved): {e}", flush=True)
    if result.get("status_changed_incident_ids") and webex_enabled:
        try:
            webex_notify_updated_incidents(result["status_changed_incident_ids"])
        except Exception as e:
            print(f"WebEx notify error (updated): {e}", flush=True)
    return result
