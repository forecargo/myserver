#!/usr/bin/env python3
"""
LINE Rich Menu setup (run once on the host).

Usage:
    pip install httpx Pillow
    python trouble-api/setup_richmenu.py
"""
import io
import os
import sys
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

# ── Load .env from repo root ──────────────────────────────────────────────────
_env = Path(__file__).resolve().parent.parent / ".env"
if _env.exists():
    for _raw in _env.read_text().splitlines():
        _raw = _raw.strip()
        if not _raw or _raw.startswith("#") or "=" not in _raw:
            continue
        _k, _, _v = _raw.partition("=")
        os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
if not TOKEN:
    sys.exit("ERROR: LINE_CHANNEL_ACCESS_TOKEN が設定されていません。")

LINE_API = "https://api.line.me/v2/bot"
DATA_API = "https://api-data.line.me/v2/bot"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# ── Button definitions ────────────────────────────────────────────────────────
#   (main_label, sub_label, send_text, bg_color)
BUTTONS = [
    ("発生中", "未解決インシデント", "発生中", "#EF4444"),
    ("一覧",   "全インシデント",   "一覧",   "#3B82F6"),
    ("同期",   "メール取込",       "同期",   "#F59E0B"),
    ("ヘルプ", "コマンド一覧",     "ヘルプ", "#22C55E"),
]

W, H = 2500, 843  # half-height rich menu (LINE recommended)
CW, CH = W // 2, H // 2


# ── Font loader ───────────────────────────────────────────────────────────────
def _find_font(size: int):
    candidates = [
        # macOS (Ventura / Sonoma)
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴ W6.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴ ProN W6.ttc",
        "/System/Library/Fonts/Supplemental/Hiragino Sans GB.ttc",
        "/Library/Fonts/Osaka.ttf",
        # Linux
        "/usr/share/fonts/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJKjp-Regular.otf",
    ]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    print("  警告: 日本語フォントが見つかりません。テキストが正しく表示されない場合があります。")
    return None


# ── Image generator ───────────────────────────────────────────────────────────
def make_image() -> bytes:
    img = Image.new("RGB", (W, H), "#111827")
    draw = ImageDraw.Draw(img)
    font_main = _find_font(160)
    font_sub = _find_font(72)

    positions = [(0, 0), (CW, 0), (0, CH), (CW, CH)]

    for (main_text, sub_text, _, color), (bx, by) in zip(BUTTONS, positions):
        # Cell background
        draw.rectangle([bx + 10, by + 10, bx + CW - 10, by + CH - 10], fill=color)

        if font_main:
            # Main label
            bb = draw.textbbox((0, 0), main_text, font=font_main)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            tx = bx + (CW - tw) // 2
            ty = by + CH // 2 - th - 15
            draw.text((tx, ty), main_text, fill="#FFFFFF", font=font_main)

            # Sub label
            if font_sub:
                sb = draw.textbbox((0, 0), sub_text, font=font_sub)
                sw, sh = sb[2] - sb[0], sb[3] - sb[1]
                sx = bx + (CW - sw) // 2
                sy = by + CH // 2 + 15
                draw.text((sx, sy), sub_text, fill="#E5E7EB", font=font_sub)

    # Divider lines
    draw.line([(CW, 0), (CW, H)], fill="#374151", width=8)
    draw.line([(0, CH), (W, CH)], fill="#374151", width=8)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── LINE API ──────────────────────────────────────────────────────────────────
def create_rich_menu() -> str:
    data = {
        "size": {"width": W, "height": H},
        "selected": True,
        "name": "障害管理メニュー",
        "chatBarText": "メニュー",
        "areas": [
            {
                "bounds": {"x": 0,  "y": 0,  "width": CW, "height": CH},
                "action": {"type": "message", "label": "発生中", "text": "発生中"},
            },
            {
                "bounds": {"x": CW, "y": 0,  "width": CW, "height": CH},
                "action": {"type": "message", "label": "一覧",   "text": "一覧"},
            },
            {
                "bounds": {"x": 0,  "y": CH, "width": CW, "height": CH},
                "action": {"type": "message", "label": "同期",   "text": "同期"},
            },
            {
                "bounds": {"x": CW, "y": CH, "width": CW, "height": CH},
                "action": {"type": "message", "label": "ヘルプ", "text": "ヘルプ"},
            },
        ],
    }
    r = httpx.post(f"{LINE_API}/richmenu", headers=HEADERS, json=data, timeout=10)
    r.raise_for_status()
    menu_id = r.json()["richMenuId"]
    print(f"  ✓ Rich menu 作成: {menu_id}")
    return menu_id


def upload_image(menu_id: str, png: bytes) -> None:
    headers = {**HEADERS, "Content-Type": "image/png"}
    r = httpx.post(
        f"{DATA_API}/richmenu/{menu_id}/content",
        headers=headers,
        content=png,
        timeout=30,
    )
    r.raise_for_status()
    print("  ✓ 画像アップロード完了")


def set_default(menu_id: str) -> None:
    r = httpx.post(
        f"{LINE_API}/user/all/richmenu/{menu_id}",
        headers=HEADERS,
        timeout=10,
    )
    r.raise_for_status()
    print("  ✓ 全ユーザーのデフォルトメニューに設定完了")


def delete_existing_menus() -> None:
    r = httpx.get(f"{LINE_API}/richmenu/list", headers=HEADERS, timeout=10)
    if r.status_code != 200:
        return
    menus = r.json().get("richmenus", [])
    for m in menus:
        mid = m["richMenuId"]
        httpx.delete(f"{LINE_API}/richmenu/{mid}", headers=HEADERS, timeout=10)
        print(f"  削除: {mid}")


if __name__ == "__main__":
    print("既存のリッチメニューを削除中...")
    delete_existing_menus()

    print("Rich menu 画像を生成中...")
    png = make_image()
    print(f"  画像サイズ: {len(png):,} bytes")

    print("LINE API に登録中...")
    menu_id = create_rich_menu()
    upload_image(menu_id, png)
    set_default(menu_id)

    print("\n✅ セットアップ完了！LINE で Bot を開くとメニューが表示されます。")
    print("   表示されない場合はトークを一度閉じて再度開いてください。")
