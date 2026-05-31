"""Vocab Extractor の共通設定。

- プロジェクトルート (`myserver/.env`) を共用して APIキーを読み込む
- Gemini クライアントを初期化してモジュールスコープで公開
- 入出力ディレクトリ・モデル名などの定数を集約
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# tango/ の親ディレクトリにある myserver/.env をロード
ROOT_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ROOT_ENV_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        f"GEMINI_API_KEY が設定されていません (期待した .env: {ROOT_ENV_PATH})"
    )

# Vision を含む構造化出力に対応する Gemini モデル
MODEL_NAME = "gemini-2.5-flash"

# 入力/出力ディレクトリ (tango/ 直下を基準とする)
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "sample_jpg"
OUTPUT_DIR = BASE_DIR / "output"

client = genai.Client(api_key=GEMINI_API_KEY)
