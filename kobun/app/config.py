"""実行時設定。

兄弟サービスに倣い ``pydantic-settings`` は使わず、``os.getenv`` で環境変数を読む。
"""

from __future__ import annotations

import os
from pathlib import Path

# kobun/ リポジトリのルート（このファイルの 2 つ上）。
BASE_DIR = Path(__file__).resolve().parent.parent

# データ・画像の所在。テストやデプロイ時に環境変数で上書き可能。
DATA_DIR = Path(os.getenv("KOBUN_DATA_DIR", str(BASE_DIR / "assets" / "data")))
ASSETS_DIR = Path(os.getenv("KOBUN_ASSETS_DIR", str(BASE_DIR / "assets")))

# 画像 URL の前置詞。``StaticFiles`` を "/assets" にマウントするため既定は空
# （= "/assets/manga/..."）。Caddy 配下では "/kobun" などを設定する。
ASSET_BASE_URL = os.getenv("KOBUN_ASSET_BASE_URL", "").rstrip("/")

# 区分（ディレクトリ名）→ 表示ラベル。
SECTION_LABELS: dict[str, str] = {
    "part1": "第一章 古文単語",
    "part2": "第二章 古文単語",
    "keigo": "敬語",
    "kanyouku": "慣用句",
}

# 単語区分（word エントリを持つ）と慣用句区分の別。
WORD_SECTIONS: tuple[str, ...] = ("part1", "part2", "keigo")
IDIOM_SECTION = "kanyouku"


def build_image_url(image_path: str | None) -> str | None:
    """JSON 内の相対パス（例 ``assets/manga/part1/001.png``）を配信 URL に変換する。

    Args:
        image_path: ``manga.image_path`` の値。``None`` ならそのまま ``None`` を返す。

    Returns:
        ``ASSET_BASE_URL`` を前置した URL。例: ``/assets/manga/part1/001.png``。
    """
    if not image_path:
        return None
    return f"{ASSET_BASE_URL}/{image_path.lstrip('/')}"
