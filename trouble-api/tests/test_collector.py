"""collector.normalize_system_name / _find_existing_incident のユニットテスト。

SQLite in-memory を使い、Incident / ProcessedEmail を直接挿入して
正規化マッチング（Pass1=完全一致 / Pass2=前方一致）の挙動を確認する。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import collector
from database import Base
from models import Incident

JST = timezone(timedelta(hours=9))


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _make(
    session: Session,
    *,
    system_name: str,
    status: str = "発生中",
    occurred_at: datetime | None,
    message_id: str,
) -> Incident:
    inc = Incident(
        system_name=system_name,
        status=status,
        occurred_at=occurred_at,
        email_received_at=occurred_at or datetime(2026, 6, 6, 8, 0, tzinfo=timezone.utc),
        email_message_id=message_id,
    )
    session.add(inc)
    session.commit()
    session.refresh(inc)
    return inc


# ---------- normalize_system_name ----------

class TestNormalize:
    def test_fenics_with_paren_equals_fenics(self):
        a = collector.normalize_system_name("FENICS（情報系NW接続の有線端末）")
        b = collector.normalize_system_name("FENICS")
        assert a == b == "fenics"

    def test_nfkc_fullwidth_ascii(self):
        assert collector.normalize_system_name("ＦＥＮＩＣＳ") == "fenics"

    def test_half_width_paren_stripped(self):
        assert collector.normalize_system_name("FENICS (legacy)") == "fenics"

    def test_collapse_whitespace(self):
        assert collector.normalize_system_name("  power   egg  ") == "power egg"

    def test_empty(self):
        assert collector.normalize_system_name(None) == ""
        assert collector.normalize_system_name("") == ""


# ---------- _find_existing_incident ----------

class TestFindExistingIncident:
    OCCURRED = datetime(2026, 6, 6, 8, 0, tzinfo=timezone.utc)

    def test_pass1_exact_match_after_normalize(self, session):
        _make(
            session,
            system_name="POWER EGG",
            occurred_at=self.OCCURRED,
            message_id="m1",
        )
        found = collector._find_existing_incident(
            session, "power egg", self.OCCURRED.isoformat()
        )
        assert found is not None and found.system_name == "POWER EGG"

    def test_pass2_prefix_match_fenics(self, session):
        """FENICS（…）が発生中、新着が FENICS だけのケース。"""
        _make(
            session,
            system_name="FENICS（情報系NW接続の有線端末）",
            occurred_at=self.OCCURRED,
            message_id="m1",
        )
        found = collector._find_existing_incident(
            session, "FENICS", self.OCCURRED.isoformat()
        )
        assert found is not None
        assert found.system_name == "FENICS（情報系NW接続の有線端末）"

    def test_pass2_reverse_prefix_match(self, session):
        """既存が短い側、新着が長い側のケースも対応。"""
        _make(
            session,
            system_name="FENICS",
            occurred_at=self.OCCURRED,
            message_id="m1",
        )
        found = collector._find_existing_incident(
            session, "FENICS（情報系NW接続の有線端末）", self.OCCURRED.isoformat()
        )
        assert found is not None and found.system_name == "FENICS"

    def test_status_resolved_is_not_matched(self, session):
        _make(
            session,
            system_name="FENICS",
            status="復旧済み",
            occurred_at=self.OCCURRED,
            message_id="m1",
        )
        found = collector._find_existing_incident(
            session, "FENICS", self.OCCURRED.isoformat()
        )
        assert found is None

    def test_out_of_window_is_excluded(self, session, monkeypatch):
        monkeypatch.setattr(collector, "INCIDENT_MATCH_WINDOW_HOURS", 72)
        _make(
            session,
            system_name="FENICS",
            occurred_at=self.OCCURRED,
            message_id="m1",
        )
        far = (self.OCCURRED + timedelta(hours=73)).isoformat()
        assert collector._find_existing_incident(session, "FENICS", far) is None

    def test_pick_closest_occurred_at(self, session):
        _make(
            session,
            system_name="FENICS",
            occurred_at=self.OCCURRED,
            message_id="m1",
        )
        near = self.OCCURRED + timedelta(hours=2)
        _make(
            session,
            system_name="FENICS（別端末）",
            occurred_at=near,
            message_id="m2",
        )
        # 新着 occurred_at は near に近いので、Pass2 候補のうち near 寄りが選ばれる
        target = (near + timedelta(minutes=10)).isoformat()
        found = collector._find_existing_incident(session, "FENICS", target)
        assert found is not None and found.system_name == "FENICS（別端末）"

    def test_empty_system_name_returns_none(self, session):
        _make(
            session,
            system_name="FENICS",
            occurred_at=self.OCCURRED,
            message_id="m1",
        )
        assert collector._find_existing_incident(session, "", self.OCCURRED.isoformat()) is None
        assert collector._find_existing_incident(session, None, None) is None

    def test_unrelated_systems_do_not_match(self, session):
        _make(
            session,
            system_name="LINE",
            occurred_at=self.OCCURRED,
            message_id="m1",
        )
        found = collector._find_existing_incident(
            session, "FENICS", self.OCCURRED.isoformat()
        )
        assert found is None

    def test_short_name_skips_pass2(self, session):
        """target_norm が 3 文字未満なら Pass2 をスキップ（誤マッチ防止）。"""
        _make(
            session,
            system_name="AI 監視システム",
            occurred_at=self.OCCURRED,
            message_id="m1",
        )
        found = collector._find_existing_incident(
            session, "AI", self.OCCURRED.isoformat()
        )
        assert found is None
