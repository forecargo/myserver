#!/usr/bin/env python3
"""
LINE Rich Menu setup (run once on the host).

Usage:
    pip install httpx Pillow
    python trouble-api/setup_richmenu.py
"""
import io
import math
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

LIFF_ID = os.getenv("LIFF_ID", "")
LIFF_URL = f"https://liff.line.me/{LIFF_ID}" if LIFF_ID else ""

LINE_API = "https://api.line.me/v2/bot"
DATA_API = "https://api-data.line.me/v2/bot"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

W, H = 2500, 843
CW, CH = W // 2, H // 2


# ── Font loader ───────────────────────────────────────────────────────────────
def _find_font(size: int):
    candidates = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴ W6.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴ ProN W6.ttc",
        "/System/Library/Fonts/Supplemental/Hiragino Sans GB.ttc",
        "/Library/Fonts/Osaka.ttf",
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


# ── Icon drawing helpers ──────────────────────────────────────────────────────
def _draw_arrowhead(draw, tip_x, tip_y, dir_x, dir_y, size, color):
    length = math.hypot(dir_x, dir_y)
    if length == 0:
        return
    dx, dy = dir_x / length, dir_y / length
    px, py = -dy, dx
    wing = size * 0.48
    bx = tip_x - dx * size
    by = tip_y - dy * size
    pts = [
        (int(tip_x), int(tip_y)),
        (int(bx + px * wing), int(by + py * wing)),
        (int(bx - px * wing), int(by - py * wing)),
    ]
    draw.polygon(pts, fill=color)


def _draw_warning(draw, cx, cy, icon_r, color, font):
    pts = [
        (cx, int(cy - icon_r)),
        (int(cx - icon_r * 0.92), int(cy + icon_r * 0.62)),
        (int(cx + icon_r * 0.92), int(cy + icon_r * 0.62)),
    ]
    draw.polygon(pts, fill=color)
    if font:
        bb = draw.textbbox((0, 0), "!", font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        draw.text((int(cx - tw // 2), int(cy - th // 2 + icon_r * 0.08)), "!", fill="#FFFFFF", font=font)
    else:
        bw = max(6, icon_r // 7)
        draw.rectangle([cx - bw//2, cy - icon_r//3, cx + bw//2, cy + icon_r//5], fill="#FFFFFF")
        dr = bw
        draw.ellipse([cx - dr, cy + icon_r//4, cx + dr, cy + icon_r//4 + dr * 2], fill="#FFFFFF")


def _draw_list(draw, cx, cy, icon_r, color):
    lw = max(5, icon_r // 10)
    pad = icon_r // 6
    x0, y0 = cx - icon_r + pad, cy - icon_r + pad
    x1, y1 = cx + icon_r - pad, cy + icon_r - pad
    try:
        draw.rounded_rectangle([x0, y0, x1, y1], radius=max(4, icon_r // 8), outline=color, width=lw)
    except AttributeError:
        draw.rectangle([x0, y0, x1, y1], outline=color, width=lw)
    inner_h = y1 - y0
    for i in (1, 2, 3):
        hy = y0 + i * inner_h // 4
        draw.line([x0 + lw, hy, x1 - lw, hy], fill=color, width=lw)
    vx = x0 + (x1 - x0) // 3
    draw.line([vx, y0 + lw, vx, y1 - lw], fill=color, width=lw)


def _draw_sync(draw, cx, cy, icon_r, color):
    lw = max(7, icon_r // 7)
    bbox = [cx - icon_r, cy - icon_r, cx + icon_r, cy + icon_r]
    draw.arc(bbox, start=200, end=340, fill=color, width=lw)
    draw.arc(bbox, start=20,  end=160, fill=color, width=lw)
    ar = lw * 2
    for angle in (340, 160):
        t = math.radians(angle)
        ax = cx + icon_r * math.cos(t)
        ay = cy + icon_r * math.sin(t)
        _draw_arrowhead(draw, ax, ay, -math.sin(t), math.cos(t), ar, color)


def _draw_help(draw, cx, cy, icon_r, color, font):
    lw = max(7, icon_r // 8)
    m = lw // 2
    draw.ellipse([cx - icon_r + m, cy - icon_r + m, cx + icon_r - m, cy + icon_r - m],
                 outline=color, width=lw)
    if font:
        bb = draw.textbbox((0, 0), "?", font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        draw.text((int(cx - tw // 2), int(cy - th // 2 - th // 10)), "?", fill=color, font=font)


# ── Image generator ───────────────────────────────────────────────────────────
def make_image() -> bytes:
    img = Image.new("RGB", (W, H), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    font_jp   = _find_font(80)
    font_en   = _find_font(50)
    font_icon = _find_font(46)

    CELLS = [
        ("発生中", "ACTIVE",  "#FEE2E2", "#DC2626", "warning"),
        ("一覧",   "HISTORY", "#EAECF0", "#3D4451", "list"),
        ("同期",   "SYNC",    "#EAECF0", "#3D4451", "sync"),
        ("ヘルプ", "SUPPORT", "#EAECF0", "#3D4451", "help"),
    ]

    circle_r = 100
    icon_r   = 54
    positions = [(0, 0), (CW, 0), (0, CH), (CW, CH)]

    for (jp, en, circle_bg, fg, icon_type), (bx, by) in zip(CELLS, positions):
        cx = bx + CW // 2
        circle_cy = by + int(CH * 0.29)

        # Circle background
        draw.ellipse([cx - circle_r, circle_cy - circle_r,
                      cx + circle_r, circle_cy + circle_r], fill=circle_bg)

        # Icon
        if icon_type == "warning":
            _draw_warning(draw, cx, circle_cy, icon_r, fg, font_icon)
        elif icon_type == "list":
            _draw_list(draw, cx, circle_cy, icon_r, fg)
        elif icon_type == "sync":
            _draw_sync(draw, cx, circle_cy, icon_r, fg)
        elif icon_type == "help":
            _draw_help(draw, cx, circle_cy, icon_r, fg, font_icon)

        # Japanese label
        text_y = circle_cy + circle_r + 18
        if font_jp:
            bb = draw.textbbox((0, 0), jp, font=font_jp)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            draw.text((cx - tw // 2, text_y), jp, fill="#1F2937", font=font_jp)
            text_y += th + 10

        # English label
        if font_en:
            en_color = fg if icon_type == "warning" else "#9CA3AF"
            sb = draw.textbbox((0, 0), en, font=font_en)
            sw = sb[2] - sb[0]
            draw.text((cx - sw // 2, text_y), en, fill=en_color, font=font_en)

    # Dividers
    draw.line([(CW, 15), (CW, H - 15)], fill="#E5E7EB", width=3)
    draw.line([(15, CH), (W - 15, CH)], fill="#E5E7EB", width=3)

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
                "action": (
                    {"type": "uri", "label": "発生中",
                     "uri": LIFF_URL + "?status=%E7%99%BA%E7%94%9F%E4%B8%AD"}
                    if LIFF_URL else
                    {"type": "message", "label": "発生中", "text": "発生中"}
                ),
            },
            {
                "bounds": {"x": CW, "y": 0,  "width": CW, "height": CH},
                "action": (
                    {"type": "uri", "label": "一覧", "uri": LIFF_URL}
                    if LIFF_URL else
                    {"type": "message", "label": "一覧", "text": "一覧"}
                ),
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
