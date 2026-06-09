"""pytest 共通設定。

trouble-api は collector.py が冒頭で `from analyzer import analyze_email`
を行う。analyzer.py は google-genai を import 時に解決するため、
テストでは google-genai を入れずに済むよう analyzer モジュールをスタブ化する。
database.py は import 時に DATABASE_URL を読むため、SQLite in-memory を設定。
"""
from __future__ import annotations

import os
import sys
import types
from pathlib import Path

# trouble-api ディレクトリをモジュール探索パスに追加
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# database.py が import 時に参照する
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# analyzer のスタブ（google-genai の依存を回避）
_analyzer_stub = types.ModuleType("analyzer")
_analyzer_stub.analyze_email = lambda subject, body, received_at: {}
sys.modules.setdefault("analyzer", _analyzer_stub)

# imapclient のスタブ（IMAP 接続は本テストでは不要）
_imap_stub = types.ModuleType("imapclient")
_imap_stub.IMAPClient = object  # 参照だけされ、生成しない
sys.modules.setdefault("imapclient", _imap_stub)
